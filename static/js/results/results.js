const stop_test = async (event) => {
    const resp = await fetch(`/api/v1/security_sast/report_status/${event.data.project_id}/${event.data.result_test_id}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            "test_status": {
                "status": "Canceled",
                "percentage": 100,
                "description": "Test was canceled"
            }
        })
    })
    resp.ok ? location.reload() : console.warn('stop test failed', resp)
}
