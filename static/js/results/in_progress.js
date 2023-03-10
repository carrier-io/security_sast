const TestProgress = {
    delimiters: ['[[', ']]'],
    props: ['test_status', 'project_id', 'test_id'],
    template: `
    <div class="card-body p-4 m-4 space-progress">
        <div class="row justify-content-center">
            <div class="col-12 text-center">
                <h4 id="test_status_status">
                    [[ status ]]
                </h4>
            </div>
            <div class="col-6">
                <div class="progress">
                    <div
                            class="progress-bar progress-bar-striped bg-success progress-bar-animated"
                            role="progressbar"
                            aria-valuenow="percentage"
                            :style="{ width: percentage + '%' }"
                            aria-valuemin="0"
                            aria-valuemax="100"
                    >
                    </div>
                </div>
            </div>
            <div class="col-12 text-center m-2 p-2">
                <h12 class="test_status_description">
                    [[ description ]]
                </h12>
            </div>
        </div>
    </div>
    `,
    data() {
        return {
            status: '',
            percentage: 0,
            description: ''
        }
    },
    mounted() {
        const {status, percentage, description} = this.test_status
        this.status = status
        this.percentage = percentage
        this.description = description
        this.poll_intrvl = setInterval(() => this.poll_updates(), 1000)
    },
    methods: {
        async poll_updates() {
            const response = await fetch(`/api/v1/security_sast/result/${this.project_id}/${this.test_id}`)
            const {test_status: {status, percentage, description}} = await response.json()
            this.status = status
            this.percentage = percentage
            this.description = description
        }
    },
    watch: {
        percentage(newValue, oldValue) {
            if (newValue === 100) {
                clearInterval(this.poll_intrvl)
                location.reload()
            }
        }
    }
}

vueApp.component('testprogress', TestProgress)