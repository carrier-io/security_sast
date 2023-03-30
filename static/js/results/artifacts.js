const artifact_download_url = `/api/v1/artifacts/security_download/${new URLSearchParams(location.search).get('result_id')}`

function artifactActionsFormatter(value, row, index) {
    return `
        <a 
            href="${artifact_download_url}/${row['name']}?test_type=sast" 
            class="fa fa-download btn-action" 
            download="${row['name']}"
        ></a>
    `
}


function testResultsQueryParams(params){
    params['test_type'] = 'sast'
    return params
}