import sys

from flask import Blueprint, render_template, request, session, current_app, jsonify, send_file, after_this_request

from gvm.connections import UnixSocketConnection
from gvm.errors import GvmError
from gvm.protocols.gmp import Gmp
from gvm.transforms import EtreeCheckCommandTransform

# initialize the blueprint
gvm_bp = Blueprint('gvm', __name__, '/gvm')

_gvm_ = dict()

# check if it's possible to connect to gvm sock
@gvm_bp.route('/gvm/check_sock')
def get_gvm_sock():
    try:
        _gvm_['connection'] = UnixSocketConnection(path='/run/gvm/gvmd.sock')
        _gvm_['transform']  = EtreeCheckCommandTransform()
        with Gmp(connection=_gvm_['connection'], transform=_gvm_['transform']) as gmp:
            response = gmp.get_version()
            print(response)
    except GvmError:
        _gvm_['connection'] = None
        _gvm_['transform'] = None
        return False

    return True

@gvm_bp.route('/gvm/login_gvm')
def login_gvm(user='gvmreader', passwd='gvmreader'):
    if _gvm_['connection'] and _gvm_['transform']:
        try:
            with Gmp(connection=_gvm_['connection'], transform=_gvm_['transform']) as gmp:
                gmp.authenticate(user, passwd)
            _gvm_['username'] = user
            _gvm_['password'] = passwd
        except GvmError as e:
            _gvm_['username'] = None
            _gvm_['password'] = None
            return False
    else:
        return False
    return True

@gvm_bp.route('/gvm/get_tasks')
def get_tasks():
    if _gvm_['connection'] and _gvm_['transform']:
        if _gvm_['username'] and _gvm_['password']:
            try:
                with Gmp(connection=_gvm_['connection'], transform=_gvm_['transform']) as gmp:
                    gmp.authenticate(_gvm_['username'], _gvm_['password'])
                    tasks = gmp.get_tasks().xpath('task')
                gvm_tasks = dict()
                for i in range(0, len(tasks)):
                    task_uuid = tasks[i].attrib['id']
                    task_name = tasks[i].find('name').text
                    task_report_count = tasks[i].find('report_count').text
                    task_report_finished = tasks[i].find('report_count/finished').text
                    task_last_report_date = tasks[i].find('last_report/report/timestamp').text
                    task_last_report_severity = tasks[i].find('last_report/report/severity').text
                    gvm_tasks[str(i+1)] = ({'id': i+1, 'uuid': task_uuid, 'name': task_name, 'count': task_report_count, 'finished': task_report_finished,
                                    'date': task_last_report_date, 'severity': task_last_report_severity})
            except GvmError:
                return 'error getting tasks'
        else:
            return 'not logged'
    else:
        return 'not connected'
    
    session['tasks'] = gvm_tasks
    return render_template('gvm_tasks.html', tasks=list(gvm_tasks.values()))

@gvm_bp.route('/gvm/get_reports_from_task/<task_id>')
def get_reports_from_task(task_id=None):
    if task_id is None:
        raise ValueError('can\'t read reports without a task id')
    
    try:
        task_uuid = session['tasks'][task_id]['uuid']
    except KeyError:
        raise KeyError(f'Task id {task_id} is not available')
    
    if _gvm_['connection'] and _gvm_['transform']:
        if _gvm_['username'] and _gvm_['password']:
            try:
                with Gmp(connection=_gvm_['connection'], transform=_gvm_['transform']) as gmp:
                    gmp.authenticate(_gvm_['username'], _gvm_['password'])
                    reports = gmp.get_reports(filter_string=f'task_id={task_uuid}').xpath('report')
                gvm_reports = dict()
                for i in range(0, len(reports)):
                    report_uuid = reports[i].attrib['id']
                    report_name = reports[i].find('name').text
                    report_start = reports[i].find('./report/scan_start').text
                    report_end = reports[i].find('./report/scan_end').text
                    report_hosts = reports[i].find('./report/hosts/count').text
                    report_vulns = reports[i].find('./report/vulns/count').text
                    gvm_reports[str(i+1)] = {'id': i+1, 'uuid': report_uuid, 'name': report_name, 'start': report_start, 
                                      'end': report_end, 'hosts': report_hosts, 'vulns': report_vulns}
            except GvmError:
                return f'error getting reports from task {task_uuid}'
        else:
            return 'not logged'
    else:
        return 'not connected'
                
    session['reports'] = gvm_reports
    
    return render_template('gvm_reports.html', reports=list(gvm_reports.values()))

@gvm_bp.route('/gvm/pick_report/<report_id>')
def pick_report(report_id=None):
    if report_id is None:
        raise ValueError('can\' pick a report without a report_id')
    
    if not 'gvm_reports' in session:
        session['gvm_reports'] = []
        
    if report_id in session['reports']:
        if session['reports'][report_id]['uuid'] not in session['gvm_reports']:
            session['gvm_reports'].append(session['reports'][report_id]['uuid'])
    else:
        raise ValueError(f'Report_id {report_id} is not available')
    
    return jsonify(session['gvm_reports'])
    
def get_results_from_report(report_uuid=None):
    if report_uuid is None:
        raise ValueError('can\'t read results without a report id')
    
    if _gvm_['connection'] and _gvm_['transform']:
        if _gvm_['username'] and _gvm_['password']:
            try:
                with Gmp(connection=_gvm_['connection'], transform=_gvm_['transform']) as gmp:
                    gmp.authenticate(username, password)
                    filter = f'report_id="{report_uuid}" and rows=10000 and sort-reverse=cvss_base and cvss_base>3.9'
                    results = gmp.get_results(filter_string=filter)
            except GvmError:
                return f'error getting results from report {report_uuid}'
        else:
            return 'not logged'
    else:
        return 'not connected'
                
    return results
                    
    
    
@gvm_bp.route('/gvm/teste')
def gvm_test():
    return 'estive aqui'

