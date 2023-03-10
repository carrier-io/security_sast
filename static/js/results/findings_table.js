
const TableCardFindings = {
    ...TableCard,
    mounted() {
        this.url = this.table_url_base

        $(() => {
            $(this.$refs.table).on('all.bs.table', function (e) {
                $('.selectpicker').selectpicker('render')
                initColoredSelect()
            })
            this.rerender()
        })

        this.register_formatters()
        console.debug('TableCardFindings mounted', {refs: this.$refs, props: this.$props})
    },
    data() {
        return {
            ...TableCard.data(),
            url: undefined,
            status_map: {
                all: '',
                valid: 'valid',
                'false positive': 'false_positive',
                ignored: 'ignored'
            },
            showModal: false,
            filtersName: [],
            loadingSave: false,
            loadingSaveAs: false,
            loadingApply: false,
            filters: null,
            selectedFilter: null,
            loadingFilters: false,
            loadingDelete: false,
            updatedFilter: null,
            severityOptions: [
                {name: 'critical', className: 'colored-select-red'},
                {name: 'high', className: 'colored-select-orange'},
                {name: 'medium', className: 'colored-select-yellow'},
                {name: 'low', className: 'colored-select-green'},
                {name: 'info', className: 'colored-select-blue'},
            ],
            statusOptions: [
                {name: 'valid', className: 'colored-select-red'},
                {name: 'false positive', className: 'colored-select-blue'},
                {name: 'ignored', className: 'colored-select-darkblue'},
                {name: 'not defined', className: 'colored-select-notdefined'},
            ],
            // tableData,
        }
    },
    methods: {
        ...TableCard.methods,
        rerender() {
            this.table_action('refresh', {
                url: this.url.href,
            })
        },
        clear_search_params() {
            this.url.searchParams.forEach((v, k) => this.url.searchParams.delete(k))
        },
        handle_status_filter(status) {
            this.clear_search_params()
            this.url.searchParams.set('status', this.status_map[status.toLowerCase()] || '')
            this.rerender()
        },
        register_formatters() {
            const selectpicker_formatter = opts => ((value, row, index, field) => {
                let options = opts.reduce((accum, {name, className},) =>
                        `${accum}<option
                        class="text-uppercase ${className}"
                        value='${name}'
                        ${name.toLowerCase() === value.toLowerCase() && 'selected'}
                    >
                        ${name}
                    </option>
                    `,
                    ''
                )
                const to_add_unexpected_value = opts.find(
                    item => item.name.toLowerCase() === value.toLowerCase()
                ) === undefined

                options += to_add_unexpected_value ? `<option value="${value}" selected>${value}</option>` : ''

                return `
                    <select
                        class="selectpicker btn-colored-select"
                        data-style="btn-colored"
                        value="${value}"
                        data-field="${field}"
                    >
                        ${options}
                    </select>
                `
            })
            window.findings_formatter_severity = selectpicker_formatter(this.severityOptions)
            window.findings_formatter_status = selectpicker_formatter(this.statusOptions)
            window.findings_eventhandler = {
                'change .selectpicker': this.handleSelectpickerChange
            }

            window.findings_formatter_details = ((index, row) => `
                <div class="col ml-3">
                    <div class="details_view">
                        <p><b>Issue Details:</b></p> ${row['details']} <br />
                    </div>
                </div>
            `)
        },
        handleSelectpickerChange(event, value, row, index) {
            // I'll leave this func here as it may be useful somewhere
            // const get_col_name = el => {
            //     const td = $(el).closest('td')
            //     const col_num = td.parent().children().index(td)
            //     return $(el).closest('table').find('thead tr').children(`:eq(${col_num})`).text().trim().toLowerCase()
            // }

            this.handleModify({
                issue_hashes: [row.issue_hash],
                [event.target.dataset.field]: event.target.value
            })
        },
        handleModify(data) {
            // const data = {
            //     issue_hashes: issueHashes,
            //     [dataType]: value
            // }
            fetch(this.url, {
                method: 'PUT',
                body: JSON.stringify(data),
                headers: {'Content-Type': 'application/json'}
            }).then(response => {
                this.rerender()
                $(document).trigger('updateSummaryEvent')
            })
        },
        bulkModify(dataType, value) {
            const issueHashes = this.table_action('getSelections').map(item => item.issue_hash)
            if (issueHashes.length > 0) {
                const data = {
                    issue_hashes: issueHashes,
                    [dataType]: value
                }
                this.handleModify(data)
            }
        },
    },
    computed: {
        ...TableCard.computed,
        table_url_base() {
            const result_test_id = new URLSearchParams(location.search).get('result_id')
            let url = new URL(`/api/v1/security_sast/findings/${getSelectedProjectId()}/${result_test_id}/`, location.origin)
            return url
        },
    }

}

register_component('TableCardFindings', TableCardFindings)

