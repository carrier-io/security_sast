const LogsApp = {
    delimiters: ['[[', ']]'],
    props: ['project_id', 'report_id'],
    data() {
        return {
            labels_api_url: '',
            logs: [],
            tags_mapper: [],
            logsSubscribed: false,
            logsSubscribedTo: null
        }
    },
    mounted() {
      console.log("Logs: mounted()")
      this.labels_api_url = `/api/v1/security_sast/loki_url/${this.project_id}/?result_id=${this.report_id}`
      this.init_logs()
    },
    template: `
        <div class="card card-12 pb-4 card-table">
            <div class="card-header">
                <div class="row">
                    <div class="col-2"><h3>Logs</h3></div>
                </div>
            </div>
            <div class="card-body card-table">
              <div class="container-logs">
                    <table id="tableLogs" class="table-logs">
                    </table>
                </div>
            </div>
        </div>
    `,
    methods: {
        init_logs() {
            console.log("Logs: init_logs()")
            fetch(this.labels_api_url, {
                method: 'GET'
            }).then(response => {
                if (response.ok) {
                    response.json().then(data => {
                      socket.on("log_data", this.logsProcess);
                      this.logsSubscribe(data.labels);
                    })
                } else {
                    console.warn('Logs failed to initialize', response)
                }
            })
        },
        logsSubscribe(labels) {
            this.logsUnsubscribe();
            this.logsSubscribed = true;
            this.logsSubscribedTo = labels;
            socket.emit("task_logs_subscribe", this.logsSubscribedTo);
        },
        logsUnsubscribe() {
            if (this.logsSubscribed) {
                socket.emit("task_logs_unsubscribe", this.logsSubscribedTo);
                this.logsSubscribedTo = null;
                this.logsSubscribed = false;
                this.tags_mapper = [];
                $('#tableLogs').empty();
            }
        },
        logsProcess(data) {
            const tagColors = [
                '#f89033',
                '#e127ff',
                '#2BD48D',
                '#2196C9',
                '#6eaecb',
                '#385eb0',
                '#7345fc',
                '#94E5B0',
            ]

            const logsTag = data.map(logTag => {
                return logTag.labels.hostname;
            })

            const uniqTags = [...new Set(logsTag)].filter(tag => !!(tag))
            uniqTags.forEach(tag => {
                if (!this.tags_mapper.includes(tag)) {
                    this.tags_mapper.push(tag);
                }
            })

            data.forEach((record_item, recordIndex) => {
                const timestamp = `<td>${this.normalizeDate(record_item)}</td>`;

                const indexColor = this.tags_mapper.indexOf(record_item.labels.hostname);
                const coloredTag = `<td><span style="color: ${tagColors[indexColor]}" class="ml-4">[${record_item.labels.hostname}]</span></td>`

                const log_level = record_item.labels.level;
                const coloredText = `<td><span class="colored-log colored-log__${log_level}">${log_level}</span></td>`

                const message = record_item.line;
                const randomIndex = Date.now() + Math.floor(Math.random() * 100);
                const row = `<tr>${timestamp}${coloredTag}${coloredText}<td class="log-message__${randomIndex}"></td></tr>`
                $('#tableLogs').append(row);
                $(`.log-message__${randomIndex}`).append(`<plaintext>${message}`);

                this.scrollLogsToEnd();
            })
        },
        normalizeDate(message_item) {
            const d = new Date(Number(message_item.time * 1000))
            const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
            return d.toLocaleString("en-GB", {timeZone: tz})
        },
        scrollLogsToEnd() {
            const elem = document.querySelector('.container-logs');
            elem.scrollTop = elem.scrollHeight;
        }
    }
}

register_component('logsapp', LogsApp)
