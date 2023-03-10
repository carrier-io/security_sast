var tableFormatters = {
    durationFormatter(value, row, index){
        return value + 's'
    },

    date_formatter(value) {
        return new Date(value).toLocaleString()
    },

    reports_test_name_button(value, row, index) {
        return `<a href="./results?result_id=${row.id}" role="button">${row.name}</a>`
    },
    reports_status_formatter(value, row, index) {
        switch (value.toLowerCase()) {
            case 'error':
            case 'failed':
                return `<div style="color: var(--red)"><i class="fas fa-exclamation-circle error"></i> ${value}</div>`
            case 'stopped':
                return `<div style="color: var(--yellow)"><i class="fas fa-exclamation-triangle"></i> ${value}</div>`
            case 'aborted':
                return `<div style="color: var(--gray)"><i class="fas fa-times-circle"></i> ${value}</div>`
            case 'finished':
                return `<div style="color: var(--info)"><i class="fas fa-check-circle"></i> ${value}</div>`
            case 'passed':
                return `<div style="color: var(--green)"><i class="fas fa-check-circle"></i> ${value}</div>`
            case 'preparing':
            case 'scanning started':
            case 'scanning finished':
            case 'processing started':
            case 'processing finished':
            case 'reporting started':
            case 'reporting finished': 
            case 'pending...':
                return `<div style="color: var(--basic)"><i class="fas fa-spinner fa-spin fa-secondary"></i> ${value}</div>`
            default:
                return value
        }
    },

    tests_actions(value, row, index) {
        return `<div class="d-flex justify-content-end">
        <button class="btn btn-default btn-xs btn-table btn-icon__xs test_run mr-2"
            data-toggle="tooltip" data-placement="top" id="test_run" title="Run Test">
            <i class="icon__18x18 icon-run"></i>
        </button>
        <div class="dropdown_multilevel">
            <button class="btn btn-default btn-xs btn-table btn-icon__xs"
                data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                <i class="icon__18x18 icon-menu-dots"></i>
            </button>
            <ul class="dropdown-menu">
                <li class="dropdown-menu_item dropdown-item d-flex align-items-center">
                    <span class="w-100 font-h5 d-flex align-items-center"><i class="icon__18x18 icon-integrate mr-1"></i>Integrate with</span>
                    <i class="icon__16x16 icon-sort"></i>
                    <ul class="submenu dropdown-menu">
                        <li class="dropdown-menu_item dropdown-item d-flex align-items-center">
                            <span class="w-100 font-h5">Docker command</span>
                        </li>
                        <li class="dropdown-menu_item dropdown-item d-flex align-items-center">
                            <span class="w-100 font-h5">Jenkins stage</span>
                        </li>
                        <li class="dropdown-menu_item dropdown-item d-flex align-items-center">
                            <span class="w-100 font-h5">Azure DevOps yaml</span>
                        </li>
                        <li class="dropdown-menu_item dropdown-item d-flex align-items-center">
                            <span class="w-100 font-h5">Test UID</span>
                        </li>
                    </ul>
                </li>
                <li class="dropdown-menu_item dropdown-item d-flex align-items-center test_edit" id="test_settings">
                    <i class="icon__18x18 icon-settings mr-2"></i><span class="w-100 font-h5">Settings</span>
                </li>
                <li id="test_delete" class="dropdown-menu_item dropdown-item d-flex align-items-center test_delete">
                    <i class="icon__18x18 icon-delete mr-2"></i><span class="w-100 font-h5">Delete</span>
                </li>
            </ul>
        </div>
        
    </div>`
    },
    tests_tools(value, row, index) {
        // todo: fix
        return Object.keys(value?.scanners || {})
    },
    source_type(value, row, index){
        return value?.name.split('_')[0]?.toUpperCase()
    },
    application_urls(value, row, index) {
        const enable_tooltip = JSON.stringify(value).length > 42  // because 42
        return `<div 
                    style="
                        max-width: 240px;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                        overflow: hidden;
                    "
                    ${enable_tooltip && 'data-toggle="infotip"'}
                    data-placement="top" 
                    title='${value}'
                >${value}</div>`
    },
    status_events: {
        "click #test_run": function (e, value, row, index) {
            apiActions.run(row.id, row.name)
        },

        "click #test_settings": function (e, value, row, index) {
            securityModal.setData(row)
            securityModal.container.modal('show')
            $('#modal_title').text('Edit Code Test')
            $('#security_test_save').text('Update')
            $('#security_test_save_and_run').text('Update And Start')

        },

        "click #test_delete": function (e, value, row, index) {
            apiActions.delete(row.id)
        }
    }
}

var artifactActions = {
    base_url: (plugin, api_name) => `/api/v1/${plugin}/${api_name}/${getSelectedProjectId()}`,
    deleteFile: async (bucketName, filename, errorHandler=()=>{}) => {
        try {
            url = artifactActions.base_url('artifacts', 'artifact') + `/${bucketName}/${filename}`
            await axios.delete(url)
        } catch (err) {
            errorHandler()          
        }
    },
    deleteBucket: async (bucketName, errorHandler=()=>{}) => {
        try{
            url = artifactActions.base_url('artifacts', 'buckets')
            await axios.delete(url, {
                params: {
                    'name': bucketName 
                }
            })
        }catch(err){
            errorHandler()
        }
    },
    uploadFile: async (file, bucketName=null, errorHandler=()=>{}) => {
        let formData = new FormData();
        formData.append('file', file)
        try {
            const response = await axios.post(`${artifactActions.base_url('security_sast', 'files')}`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                },
                params: {
                    bucket: bucketName
                }
            })
            data = response['data']
            return data['item']
        } catch(err){
            errorHandler()
        }        
    },
}

var apiActions = {
    base_url: api_name => `/api/v1/security_sast/${api_name}/${getSelectedProjectId()}`,
    run: (id, name) => {
        fetch(`${apiActions.base_url('test')}/${id}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({'test_name': name})
        }).then(response => response.ok && apiActions.afterSave())
    },
    delete: ids => {
        const url = `${apiActions.base_url('tests')}?` + $.param({"id[]": ids})
        fetch(url, {
            method: 'DELETE'
        }).then(response => response.ok && apiActions.afterSave())
    },
    edit: async (testUID, data) => {
        apiActions.beforeSave()
        data = await apiActions.handleFileUploading(data, testUID)
        fetch(`${apiActions.base_url('test')}/${testUID}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        }).then(response => {
            apiActions.afterSave()
            if (response.ok) {
                securityModal.container.modal('hide');
            } else {
                response.json().then(data => securityModal.setValidationErrors(data))
            }
        })
    },
    editAndRun: (testUID, data) => {
        data['run_test'] = true
        return apiActions.edit(testUID, data)
    },
    create: async data => {
        apiActions.beforeSave()
        data = await apiActions.handleFileUploading(data)
        fetch(apiActions.base_url('tests'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        }).then(response => {
            apiActions.afterSave()
            if (response.ok) {
                $("#createApplicationTest").modal('hide');
            } else {
                response.json().then(data => securityModal.setValidationErrors(data))
            }
        })
    },
    createAndRun: data => {
        data['run_test'] = true
        return apiActions.create(data)
    },
    currentTestData: testUID => {
        currentValue = $("#application_tests_table").bootstrapTable("getData", params={useCurrentPage: true}).filter(
            row => row['test_uid'] == testUID
        )[0]
        return currentValue
    },
    
    handleFileUploading: async (data, testUID=null) => {
        if (data['source']['name'] != "artifact"){
            if (testUID){
                currentValue = apiActions.currentTestData(testUID)
                if (currentValue['source']['name'] == "artifact"){
                    bucket = currentValue['source']['file_meta']['bucket']
                    artifactActions.deleteBucket(bucket, () => {
                        showNotify("ERROR", "Artifact uploading failed")
                        $("#security_test_save").removeClass("disabled updating")
                        $("#security_test_save_and_run").removeClass("disabled updating")
                    })
                }   
            }
            return data
        }
        file = data['source']['file']
        // if it is update operation and file is not set
        // then set current source values
        if (!file && testUID){
            currentValue = apiActions.currentTestData(testUID)
            data['source'] = currentValue['source']
            return data
        }
        // if update operation then delete previous artifact
        bucket = null
        if (testUID){
            currentValue = apiActions.currentTestData(testUID)
            if (currentValue['source']['name'] == "artifact"){
                bucket = currentValue['source']['file_meta']['bucket']
                filename = currentValue['source']['file_meta']['filename']
                artifactActions.deleteFile(bucket, filename, () => {
                    showNotify("ERROR", "Artifact uploading failed")
                    $("#security_test_save").removeClass("disabled updating")
                    $("#security_test_save_and_run").removeClass("disabled updating")
                })
            }
        }

        const fileMeta = await artifactActions.uploadFile(file, bucket, () => {
            showNotify("ERROR", "Artifact uploading failed")
            $("#security_test_save").removeClass("disabled updating")
            $("#security_test_save_and_run").removeClass("disabled updating")
        })

        if (fileMeta == null)
            return
 
        data['source']['name'] = "artifact"
        data['source']['file_meta'] = fileMeta
        data['source']['file'] = fileMeta['filename']
        return data
    },
    beforeSave: () => {
        $("#security_test_save").addClass("disabled updating")
        $("#security_test_save_and_run").addClass("disabled updating")
        securityModal.clearErrors()
        alertCreateTest?.clear()
    },
    afterSave: () => {
        $("#application_tests_table").bootstrapTable('refresh')
        $("#results_table").bootstrapTable('refresh')
        $("#security_test_save").removeClass("disabled updating")
        $("#security_test_save_and_run").removeClass("disabled updating")
    },
    results_delete: ids => {
        const url = `${apiActions.base_url('results')}?` + $.param({"id[]": ids})
        fetch(url, {
            method: 'DELETE'
        }).then(response => response.ok && vueVm.registered_components.table_results?.table_action('refresh'))
    },
}

$(document).on('vue_init', () => {

    $('#delete_test').on('click', e => {
        const ids_to_delete = $(e.target).closest('.card').find('table.table').bootstrapTable('getSelections').map(
            item => item.id
        ).join(',')
        ids_to_delete && apiActions.delete(ids_to_delete)
    })

    $('#delete_results').on('click', e => {
        const ids_to_delete = vueVm.registered_components.table_results?.table_action('getSelections').map(
            item => item.id
        ).join(',')
        ids_to_delete && apiActions.results_delete(ids_to_delete)
    })

    $("#application_tests_table").on('all.bs.table', initTooltips)

    socket.on("result_status_updated", data => {
        result_id = data['result_id']
        result_status = data['status']
        $('#results_table').bootstrapTable('updateByUniqueId', {
            id: result_id,
            row: {
                'test_status.status': result_status['status']
            }
        })

    })
})
