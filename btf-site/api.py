import os
from io import StringIO, BytesIO

import yaml
from yaml.dumper import SafeDumper
from yaml.loader import SafeLoader
import tempfile

from flask import Blueprint, render_template, request, session, current_app, jsonify, send_file, after_this_request
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask_session import Session

api_bp = Blueprint('api', __name__, url_prefix='/api')

#
# route to upload xml reports
@api_bp.route('/xml_reports', methods=['POST'])
def upload_xml_reports():
    if 'files[]' not in request.files:
        return 'No file uploaded. try again.'
    
    # if any file where uploaded before, remove
    erase_xml_reports()
    
    # now save all files        
    lines = []

    files = request.files.getlist('files[]')
    for file in files:
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            lines.append(file.filename)
            
    session['xml_reports'] = lines
    print(session['xml_reports'])
    
    return render_template('boxed_results.html', lines=lines)   

#
# route to erase all xml reports previously uploaded
@api_bp.route('/erase_xml_reports', methods=['POST'])
def erase_xml_reports():
    # if any file where uploaded before, remove
    if 'xml_reports' in session:
        for filename in session['xml_reports']:
            xml_report_path = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(filename))
            try: 
                os.remove(xml_report_path)
            except FileNotFoundError:
                pass
        
        session.pop('xml_reports')
    

    return 'OK'

#
# routes to include filters 
@api_bp.route('/networks_includes', methods=['POST'])
@api_bp.route('/networks_excludes', methods=['POST'])
@api_bp.route('/regex_includes', methods=['POST'])
@api_bp.route('/regex_excludes', methods=['POST'])
@api_bp.route('/cve_includes', methods=['POST'])
@api_bp.route('/cve_excludes', methods=['POST'])
def upload_filter_file():
    if 'files[]' not in request.files:
        return '<span class="erasedbox">não recebi nada</span>'

    files = request.files.getlist('files[]')
    fp = FileStorage(files[0])
    memfile = fp.stream.read().decode('UTF-8')
     
    filter_list = []
    
    for line in memfile.splitlines():
        if line != '':
            filter_list.append(line)
    
    filter_name = request.form.get('input_field_name', None)
    if not filter_name is None:
        [filter_class, filter_option] = filter_name.split('_')

        if not filter_class in session['config']:
            session['config'][filter_class] = dict()
            
        session['config'][filter_class][filter_option] = filter_list

    return render_template('boxed_results.html', lines=filter_list)   

#
# route to erase filters previously uploaded
@api_bp.route('/erase_networks_includes', methods=['POST'])
@api_bp.route('/erase_networks_excludes', methods=['POST'])
@api_bp.route('/erase_regex_includes', methods=['POST'])
@api_bp.route('/erase_regex_excludes', methods=['POST'])
@api_bp.route('/erase_cve_includes', methods=['POST'])
@api_bp.route('/erase_cve_excludes', methods=['POST'])
def clean_filter_option():
    filter_name = request.form.get('input_field_name', None)
    if not filter_name is None:
        [filter_class, filter_option] = filter_name.split('_')
        if filter_class in session['config']:
            if filter_option in session['config'][filter_class]:
                session['config'][filter_class].pop(filter_option)
            if len(session['config'][filter_class]) == 0:
                session['config'].pop(filter_class)
            resp = jsonify({'message': 'OK'})
            resp.status = 200
        else:
            resp = jsonify({'message': f'filter {filter_class} {filter_option} not set'})
            resp.status = 200
    else:
        resp = jsonify({'message': 'no filter name received. no teapot for you'})
        resp.status = 200
        
    return resp
    
#
# routes to set option flags
@api_bp.route("/set_level_flag", methods=['POST'])
@api_bp.route("/set_reporttype_flag", methods=['POST'])
@api_bp.route("/set_format_flag", methods=['POST'])
def set_flag():
    flag_field = request.form.get('flag_field', None)
    
    if not flag_field is None:
        value = request.form.get('value', None)
        if not value is None:
            session['config'][flag_field] = value
                
    resp = jsonify({'message': 'OK'})
    resp.status = 200
    
    return resp

#
# route to load configuration .yml file. the xml_reports, if already loaded, will not be changed
@api_bp.route("/upload_configuration", methods=['POST'])
def upload_configuration():
    if 'files[]' not in request.files:
        return '<span class="erasedbox">não recebi nada</span>'

    files = request.files.getlist('files[]')
    fp = FileStorage(files[0])
    with StringIO(fp.stream.read().decode('UTF-8')) as memfile:
        configs_read = yaml.load(memfile.read(), Loader=SafeLoader)
    
    # erases all previous configuration but preserves xml_reports already loaded
    session.pop('config')
    session['config'] = dict()
    
    resp = dict()
    
    # flags not in .yaml file will be set to default
    if 'level' in configs_read:
        resp['level'] = configs_read['level']
        session['config']['level'] = configs_read['level']
    else:
        resp['level'] = 'none'
        session['config']['level'] = 'none'

    if 'reporttype' in configs_read:
        resp['reporttype'] = configs_read['reporttype']
        session['config']['reporttype'] = configs_read['reporttype']
    else:
        resp['reporttype'] = 'none'
        session['config']['reporttype'] = 'none'
    
    if 'format' in configs_read:
        resp['format'] = configs_read['format']
        session['config']['format'] = configs_read['format']
    else:
        resp['format'] = 'none'
        session['config']['format'] = 'none'
    
    for filter in ['networks', 'regex', 'cve']:
        if filter in configs_read:
            if 'includes' in configs_read[filter]:
                resp['show_' + filter + 'includes'] = render_template('boxed_results.html', lines=configs_read[filter]['includes'])
                if not filter in session['config']:
                    session['config'][filter] = dict()
                session['config'][filter]['includes'] = configs_read[filter]['includes']
            if 'excludes' in configs_read[filter]:
                resp['show_' + filter + 'excludes'] = render_template('boxed_results.html', lines=configs_read[filter]['excludes'])
                if not filter in session['config']:
                    session['config'][filter] = dict()
                session['config'][filter]['excludes'] = configs_read[filter]['excludes']
    
    resp['status'] = 200
    
    return jsonify(resp), 200

#
# sends a .yml file with the current configuration as attachment
@api_bp.route("/save_configuration", methods=['GET'])
def save_configuration():
    
    fp = BytesIO(yaml.dump(session['config'], Dumper=SafeDumper).encode())
    
    return send_file(fp, as_attachment=True, download_name='new_config.yml')

#
# user has just landed on this page or is reloading or clearing the configuration. set all configuration defaults
@api_bp.route("/clear_configuration", methods=['POST'])
def new_session_configuration():
    
    if 'xml_reports' in session:
        erase_xml_reports()
    
    try:
        session.pop('config')
    except:
        pass
    
    session['config'] = dict()
        
    session['config']['level'] = 'none'
    session['config']['reporttype'] = 'vulnerability'
    session['config']['format'] = 'xlsx'

    resp = session['config']
    resp['status'] = 200

    # remove ou prepara remoção de arquivos temporarios
    if 'tmp_files_to_remove' in session:
        for file_path in session['tmp_files_to_remove']:
            try:
                os.remove(file_path)
            except:
                pass

    session['tmp_files_to_remove'] = []

    return jsonify(resp), 200

#
# generate the report with openvasreporting and send it back as attachment
@api_bp.route("/generate_report", methods=['GET', 'POST'])
def generate_report():
    
    # check if xml_reports exists and are all loaded in tmp dir
    fullpath_filenames = []
    if 'xml_reports' in session:
        for filename in session['xml_reports']:
            fullpath_filename = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(filename))
            if not os.path.exists(fullpath_filename):
                return f"could not find loaded file {secure_filename(filename)}."
            fullpath_filenames.append(fullpath_filename)
    else:
        return jsonify("Please load at least one openvas xml report before converting")
    
    # saves current configuration in tmp file
    config_file_fp, config_file_path = tempfile.mkstemp(suffix='.yml')
    with open(config_file_path, 'w') as t:
        yaml.dump(session['config'], t, Dumper=SafeDumper)
        
    # generates the report
    from openvasreporting import Config_YAML, convert
    
    report_file_fp, report_file_path = tempfile.mkstemp(suffix="." + session['config']['format'])
    config = Config_YAML(fullpath_filenames, config_file_path, report_file_path)
    convert(config)
    
    session['tmp_files_to_remove'].append(report_file_path)
    os.remove(config_file_path)
        
    return send_file(report_file_path, as_attachment=True, download_name='openvas_report.' + session['config']['format'])
