/* just pops a message using a field that gets visible when not empty
   receives: message to be poped
*/
function pop_message(message) {
    $('#show_message').html(message)
    setTimeout(function() {
       $('#show_message').html('');
    }, 3000);
    return;
 }

/* shows request response at #show_{input_div} */
function show_response (input_id, response) {
    var show_input_id = '#show_' + input_id; 
    var load_input_id = '#load_' + input_id;
    $(show_input_id).css('display', 'block');
    $(load_input_id).css('display', 'none');

    $(show_input_id).html(response);
    
    //$('#' + input_id).reset();

    return;
};

/* shows a waiting gif at #show_{input_div} */
function show_waiting(input_id) {
    var show_input_id = '#show_' + input_id; 
    var load_input_id = '#load_' + input_id;
    $(show_input_id).css('display', 'block');
    $(load_input_id).css('display', 'none');

    /* ==> const WAITING_IMAGE_URL must be set before calling this script. */
    $(show_input_id).html('<div class="col-12 mw-100 mh-100 text-center align-middle"><img class="imgwaiting" src="' + WAITING_IMAGE_URL + '"></div>'); 
    
    return;
};

/* function to erase uploaded xml reports */
function erase_uploaded_files (server_url, input_id) {
    var show_input_id = '#show_' + input_id; 
    var load_input_id = '#load_' + input_id;

    $.ajax({
        url: '/api/erase_xml_reports',
        cache: false,
        contentType: false,
        processData: false,
        data: false,
        type: 'post',
        success: function(response) {
            if (response.status == 'success') {
                $(show_input_id).html('');
                $(show_input_id).css('display', 'none');
                $(load_input_id).css('display', 'block');
                pop_message('Uploaded xml reports erased')
            } else if (response.status == 'error') {
                pop_message(response.message)
            }
        }
    });
    
};

/* function to erase filters uploaded 
 * receives:
 *    the server_url to be used
 *    the id of the input field used to upload filters 
*/
function erase_filter(server_url, input_id) {
    var form_data = new FormData();

    show_input_id = '#show_' + input_id;
    load_input_id = '#load_' + input_id;
    
    form_data.append('input_field_name', input_id);

    $.ajax({
        url: server_url,
        cache: false,
        contentType: false,
        processData: false,
        data: form_data,
        type: 'post',
        success: function (response) {
            if (response.status == 'success') {
                $(show_input_id).html('');
                $(show_input_id).css('display', 'none');
                $(load_input_id).css('display', 'block');
                pop_message(response.message)
            }
        },
        error: function (response) {
            pop_message(response.message)
        }
    });

    return;
}

/* function to set config flags
 * receives:
 *    the server_url to be used
 *    the id of the input field used to upload filters 
*/
function set_flag(server_url, input_name) {
    var form_data = new FormData();
    
    form_data.append('flag_field', input_name);
    var selector = 'input[type="radio"][name="' + input_name + '"]:checked'
    var value = document.querySelector(selector).value
    form_data.append('value', value);

    $.ajax({
        url: server_url,
        cache: false,
        contentType: false,
        processData: false,
        data: form_data,
        type: 'post',
        success: function() {
            if (input_name.match(/format/)) {
              var imgsrc = src='' + IMAGES_URL_BASE + '/format-' + value + '.svg' ;
              $('#generate_report').attr('src', imgsrc);
            }
        }
    });
 
    return;
};

/* function to upload a configuration from a yaml formatted file.
 * receives:
 *    the server_url to be used
 *    the id of the input field to be used 
*/
function upload_configuration (server_url, input_id, msg_id) {
                var form_data = new FormData();
                var ins = document.getElementById(input_id).files.length;

                msg_id = '#' + msg_id;
                /* ==> const WAITING_IMAGE_URL must be set before including this script. */
                $(msg_id).html('<div class="imgbox"><img class="imgwaiting" src="' + WAITING_IMAGE_URL + '"></div>');

                if (ins == 0) {
                    $(msg_id).html('<span style="color:red">Select at least one file</span>');
                    return;
                }

                form_data.append('files[]', document.getElementById(input_id).files[0]);
                
                form_data.append('input_field_name', input_id);

                $.ajax({
                    url: server_url,
                    cache: false,
                    contentType: false,
                    processData: false,
                    data: form_data,
                    type: 'post',
                    success: function (response) {
                        $(msg_id).html(response.status);
                        if (response.level) {
                            document.getElementById('level' + '_' + response.level).checked = true;
                        }
                        if (response.reporttype) {
                            document.getElementById('reporttype' + '_' + response.reporttype).checked = true;
                        }
                        if (response.format) {
                            document.getElementById('format' + '_' + response.format).checked = true;
                        }
                        if (response.networks_includes) {
                            show_response('networks_includes', response.networks_includes);
                        } 
                        if (response.networks_excludes) {
                            show_response('networks_excludes', response.networks_excludes);
                        } 
                        if (response.regex_includes) {
                            show_response('regex_includes', response.regex_includes);
                        } 
                        if (response.regex_excludes) {
                            show_response('regex_excludes', response.regex_excludes);
                        } 
                        if (response.cve_includes) {
                            show_response('cve_includes', response.cve_includes);
                        } 
                        if (response.cve_excludes) {
                            show_response('cve_excludes', response.cve_excludes);
                        } 
                    },
                    error: function (response) {
                        $(msg_id).html(response);
                    }
                });

                return;
};

/* function to reset configuration fields */
function reset_configuration() {
    document.getElementById('level_none').checked = true;
    document.getElementById('reporttype_vulnerability').checked = true;
    document.getElementById('format_xlsx').checked = true;
    $('#show_networks_includes').html('');
    $('#show_networks_excludes').html('');
    $('#show_regex_includes').html('');
    $('#show_regex_excludes').html('');
    $('#show_cve_includes').html('');
    $('#show_cve_excludes').html('');
}

/* function to clear the configuration
 * receives:
 *    the server_url to be used
*/
function clear_configuration (server_url) {

    $.ajax({
        url: server_url,
        cache: false,
        contentType: false,
        processData: false,
        data: '',
        type: 'post',
        success: function (response) {
           reset_configuration();
        },
        error: function (response) {
            $('#msgbox').html(response)
        }
    });

    return;
};

/* function to generate and download a report with the current configuration
 * receives:
 * a id where error messages can be written
*/
function generate_report(msg_id) {
    $('#generate_report').attr('src', WAITING_IMAGE_URL)
    $.ajax({
        type: "POST",
        url: "/api/generate_report",
        data: '',
        contentType: false,
        processData: false,
        xhr: function() {
            var xhr = new XMLHttpRequest();
            xhr.contentType
            xhr.onreadystatechange = function() {
                if (xhr.readyState == 2) {
                    if (xhr.getAllResponseHeaders().indexOf('text/text') > 0) {
                        xhr.responseType = "json";
                    } else {
                        xhr.responseType = "blob";
                    }
                }
            };
            return xhr;
        },
        success: function(response, status, xhr) {
            var x = 1;
            if (response.status == 'error') {
                pop_message(response.message)
            } else {           
                // check for a filename
                var blob = response
                var filename = "";
                var disposition = xhr.getResponseHeader('Content-Disposition');
                if (disposition && disposition.indexOf('attachment') !== -1) {
                    var filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                    var matches = filenameRegex.exec(disposition);
                    if (matches != null && matches[1]) filename = matches[1].replace(/['"]/g, '');
                } else {
                    pop_message('<span class="erasedbox">' + typeof(blob) + '</span>');
                }
        
                var URL = window.URL || window.webkitURL;
                var downloadUrl = URL.createObjectURL(blob);
        
                if (filename) {
                    var a = document.createElement("a");
                    a.href = downloadUrl;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    $('body').remove(a);
                } else {
                    window.location.href = downloadUrl;
                }
                setTimeout(function () { URL.revokeObjectURL(downloadUrl); }, 100); // cleanup
           }
        },
        error: function(response, status, xhr) {
            pop_message(status)
        },
        complete: function() {
            var selector = 'input[type="radio"][name="format"]:checked'
            var value = document.querySelector(selector).value
            var imgsrc = src='' + IMAGES_URL_BASE + '/format-' + value + '.svg' ;
            $('#generate_report').attr('src', imgsrc) ;
        }
    });
}

function other_theme() {
    $.ajax({
        url: '/api/next_theme',
        cache: false,
        contentType: false,
        processData: false,
        data: '',
        type: 'post',
        success: function (response) {
            window.location.reload( false );
            reset_configuration();
        },
    });

    return;
}