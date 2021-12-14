import os
from io import StringIO, BytesIO

from .libs.utils import size_format, valid_xml, valid_network, valid_regex, valid_cve, make_data_table

import yaml
from yaml.dumper import SafeDumper
from yaml.loader import SafeLoader
import tempfile

from flask import Blueprint, render_template, session, jsonify, request, current_app, Markup, escape, send_file
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask_session import Session

api_bp = Blueprint('api', __name__, url_prefix='/api')

#
# route to upload xml reports
@api_bp.route('/xml_reports', methods=['POST'])
def upload_xml_reports():
    # if any file where uploaded before, remove
    erase_xml_reports()
    
    # now save all files        
    lines = []
    dataTable = []

    files = request.files;
    i = 1
    for item in files:
        file = files.get(item)
        if file:
            filename = secure_filename(file.filename)
            secure_name = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(secure_name)
            
            if not valid_xml(secure_name):
                return Markup(f'<span class="erasedbox">File {filename} is not a valid Greenbone Security Assistant XML Report</span>')
            
            lines.append(filename)
            filesize = os.path.getsize(secure_name)
            filetype = file.content_type.split('/')[1]
            dataTable.append({'id': i, 'filename': secure_filename(file.filename), 'type': filetype, 'size': size_format(filesize)})
            i = i + 1
            
    session['xml_reports'] = lines
    
    return render_template('boxed_results.html', lines=dataTable, show_header=False,
                           colgroup_classes=('col-1', 'col-auto', 'col-2', 'col-2'), primary_key='id') 


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
    file = request.files['file[0]']
    fp = FileStorage(file)
    memfile = fp.stream.read().decode('UTF-8')
     
    filter_list = []
    
    filter_name = request.args.get('input_field_name', None)
    if not filter_name is None:
        [filter_class, filter_option] = filter_name.split('_')
        if not filter_class in session['config']:
            session['config'][filter_class] = dict()

        i = 1
        dataTable = []
        for line in memfile.splitlines():
            if line != '':
                if filter_class == 'networks' and not valid_network(escape(line)):
                    return Markup(f'<span class="erasedbox">line {i} in {file.filename} is not a valid IP, IP-Range or Network CIDR:<br />{escape(line)}.</span>')
                if filter_class == 'regex' and not valid_regex(escape(line)):
                    return Markup(f'<span class="erasedbox">line {i} in {file.filename} is not a valid regular expression:<br />{escape(line)}.</span>')
                if filter_class == 'cve' and not valid_cve(escape(line)):
                    return Markup(f'<span class="erasedbox">line {i} in {file.filename} is not a valid CVE ID [CVE-yyyy-n+]:<br />{escape(line)}.</span>')
                    
                filter_list.append(line)
                dataTable.append({'id': i, filter_name: line})
                i = i + 1
    
        session['config'][filter_class][filter_option] = filter_list

    return render_template('boxed_results.html', lines=dataTable, colgroup_classes=('col-1', 'col-auto'), show_header=False,
                           primary_key='id') 


#
# route to erase filters previously uploaded
@api_bp.route('/erase_networks_includes', methods=['POST'])
@api_bp.route('/erase_networks_excludes', methods=['POST'])
@api_bp.route('/erase_regex_includes', methods=['POST'])
@api_bp.route('/erase_regex_excludes', methods=['POST'])
@api_bp.route('/erase_cve_includes', methods=['POST'])
@api_bp.route('/erase_cve_excludes', methods=['POST'])
def clean_filter_option():
    print('aqui')
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
        return Markup('<span class="erasedbox">não recebi nada</span>')

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
    
    if 'networks' in configs_read:
        if not 'networks' in session['config']:
            session['config']['networks'] = dict()
        if 'includes' in configs_read['networks']:
            for l in configs_read['networks']['includes']:
                if not valid_network(escape(l)):
                    resp['networks_includes'] = Markup(f'<span class="erasedbox">Invalid IP, IP Range or Network CIDR in networks.includes:<br />{escape(l)}.</span>')
                    break
            if not 'networks_includes' in resp:
                resp['networks_includes'] = render_template('boxed_results.html', show_headers=True,
                               lines=make_data_table(lines=configs_read['networks']['includes'], header='networks'),
                               colgroup_classes=('col-1', 'col-auto'),
                               primary_key='id', primary_key_title='#')
                session['config']['networks']['includes'] = configs_read['networks']['includes']
        if 'excludes' in configs_read['networks']:
            for l in configs_read['networks']['excludes']:
                if not valid_network(l):
                    resp['networks_excludes'] = Markup(f'<span class="erasedbox">Invalid IP, IP Range or Network CIDR in networks.excludes:<br />{escape(l)}.</span>')
                    break
            if not 'networks_excludes' in resp:
                resp['networks_excludes'] = render_template('boxed_results.html', 
                               lines=make_data_table(lines=configs_read['networks']['excludes'], header='networks'),
                               colgroup_classes=('col-1', 'col-auto'), titles=[('id', '#'), ('networks', 'excludes')], primary_key='id')
                session['config']['networks']['excludes'] = configs_read['networks']['excludes']
    
    if 'regex' in configs_read:
        if not 'regex' in session['config']:
            session['config']['regex'] = dict()
        if 'includes' in configs_read['regex']:
            for l in configs_read['regex']['includes']:
                if not valid_regex(escape(l)):
                    resp['regex_includes'] = f'<span class="erasedbox">Invalid regular expression in regex.includes:<br />{escape(l)}.</span>'
                    break
            if not 'regex_includes' in resp:
                resp['regex_includes'] = render_template('boxed_results.html', 
                               lines=make_data_table(lines=configs_read['regex']['includes'], header='regex'),
                               colgroup_classes=('col-1', 'col-auto'),
                               titles=[('id', '#'), ('regex', 'includes')], primary_key='id')
                session['config']['regex']['includes'] = configs_read['regex']['includes']
        if 'excludes' in configs_read['regex']:
            for l in configs_read['regex']['excludes']:
                if not valid_regex(escape(l)):
                    resp['regex_excludes'] = f'<span class="erasedbox">Invalid regular expression in regex.excludes:<br />{escape(l)}.</span>'
                    break
            if not 'regex_excludes' in resp:
                resp['regex_excludes'] = render_template('boxed_results.html', 
                               lines=make_data_table(lines=configs_read['regex']['excludes'], header='regex'),
                               colgroup_classes=('col-1', 'col-auto'),
                               titles=[('id', '#'), ('regex', 'excludes')], primary_key='id')
                session['config']['regex']['excludes'] = configs_read['regex']['excludes']
    
    if 'cve' in configs_read:
        if not 'cve' in session['config']:
            session['config']['cve'] = dict()
        if 'includes' in configs_read['cve']:
            for l in configs_read['cve']['includes']:
                if not valid_cve(escape(l)):
                    resp['cve_includes'] = f'<span class="erasedbox">Invalid CVE id in cve.includes:<br />{escape(l)}.</span>'
                    break
            if not 'cve_includes' in resp:
                resp['cve_includes'] = render_template('boxed_results.html', 
                               lines=make_data_table(lines=configs_read['cve']['includes'], header='cve'),
                               colgroup_classes=('col-1', 'col-auto'),
                               titles=[('id', '#'), ('cve', 'includes')], primary_key='id')
                session['config']['cve']['includes'] = configs_read['cve']['includes']
        if 'excludes' in configs_read['cve']:
            for l in configs_read['cve']['excludes']:
                if not valid_cve(escape(l)):
                    resp['cve_excludes'] = f'<span class="erasedbox">Invalid CVE id in cve.excludes:<br />{escape(l)}.</span>'
                    break
            if not 'cve_excludes' in resp:
                resp['cve_excludes'] = render_template('boxed_results.html', show_table=True,
                               lines=make_data_table(lines=configs_read['cve']['excludes'], header='cve'),
                               colgroup_classes=('col-1', 'col-auto'),
                               titles=[('id', '#'), ('cve', 'excludes')], primary_key='id')
                session['config']['cve']['excludes'] = configs_read['cve']['excludes']

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

    if 'gvm_reports' in session:
        session.pop('gvm_reports')
        
    if 'tasks' in session:
        session.pop('tasks')
        
    if 'reports' in session:
        session.pop('reports')
    
    session['config'] = dict()
        
    session['config']['level'] = 'none'
    session['config']['reporttype'] = 'vulnerability'
    session['config']['format'] = 'xlsx'

    resp = session['config']

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
                return Markup(f"could not find loaded file {secure_filename(filename)}.")
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

# just to have fun
@api_bp.route('/next_theme', methods=['POST'])
def next_theme():
    
    print(f"current theme: {current_app.config['BOOTSTRAP_BOOTSWATCH_THEME']}")
    
    themes = ['cosmo', 'flatly', 'journal', 'litera', 'pulse', 
              'sandstone', 'slate', 'solar', 'spacelab', 'superhero', 'united']
    
    current_theme = current_app.config['BOOTSTRAP_BOOTSWATCH_THEME']
    current_theme_index = themes.index(current_theme)
    
    if current_theme_index+1 == len(themes):
        current_app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = themes[0]
    else:
        current_app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = themes[current_theme_index+1]

    # resets configuration - document will be reloaded at return to show new theme
    new_session_configuration()
    
    print(f"new theme: {current_app.config['BOOTSTRAP_BOOTSWATCH_THEME']}")

    return '200'
