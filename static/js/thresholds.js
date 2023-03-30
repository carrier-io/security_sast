const api_th_base_url = '/api/v1/security_sast'
const ThresholdModal = {
    props: ['modal_id', 'thresholds_table_component_name', 'tests_table_component_name', 'threshold_params_id'],
    delimiters: ['[[', ']]'],
    data() {
        return this.initial_state()
    },
    mounted() {
        $(this.$el).on('hide.bs.modal', this.clear)
        $(this.$el).on('show.bs.modal', () => {
            this.test_options = vueVm.registered_components[
                this.$props.tests_table_component_name
            ]?.table_action('getData').reduce((accum, item) => {
                accum.push(item.name)
                return accum
            }, [])
        })
    },
    template: `<div class="modal modal-small fixed-left fade shadow-sm" tabindex="-1" role="dialog" 
            :id="modal_id"
    >
    <div class="modal-dialog modal-dialog-aside" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <div class="row w-100">
                    <div class="col">
                        <h2>[[ mode === 'update' ? 'Update' : 'Create' ]] threshold</h2>
                    </div>
                    <div class="col-xs">
                        <button type="button" class="btn  btn-secondary mr-2" data-dismiss="modal" aria-label="Close">
                            Cancel
                        </button>
                        <button type="button" class="btn btn-basic"
                            :disabled="is_fetching"
                            @click="() => mode === 'update' ? handle_update_threshold() : handle_create_threshold()"
                        >
                            [[ mode === 'update' ? 'Update' : 'Save' ]]
                        </button>
                    </div>
                </div>
            </div>
            <div class="modal-body">
                <div class="section">

                    <div class="row">
                        <div class="d-flex flex-column w-100 mb-3">
                            <h5 class="pt-2">Test</h5>
                            <select class="selectpicker bootstrap-select__b" data-style="btn"
                                v-model="test"
                                @change="handle_change_test"
                                :disabled="mode !== 'create'"
                            >
                                <option v-for="test in test_options" :value="test">[[ test ]]</option>
                            </select>
                            <div class="invalid-feedback" style="display: block;">[[ errors.test ]]</div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="d-flex flex-column w-100  mb-3">
                            <h5 class="pt-2">Test context/scope</h5>
                            <select class="selectpicker bootstrap-select__b" data-style="btn"
                                v-model="scope"
                                @change="handle_change_scope"
                                :disabled="mode !== 'create'"
                            >
                                <option v-for="scope in scope_options" :value="scope">[[ scope ]]</option>
                            </select>
                            <div class="invalid-feedback" style="display: block;">[[ errors.scope ]]</div>
                        </div>
                    </div>

                    <div class="mt-3">
                        <slot name='params_table'></slot>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
    
    `,
    watch: {
        test_options() {
            this.$nextTick(this.update_pickers)
        },
        scope_options() {
            this.$nextTick(this.update_pickers)
        },
        scope(newValue, oldValue){
            if (!oldValue){
                delete this.errors['scope']
            }
        },
        test(newValue, oldValue){
            if (!oldValue){
                delete this.errors['test']
            }
        }

    },
    computed: {
        test_parameters() {
            return ThresholdParamsTable.Manager(this.$props.threshold_params_id)
        },
    },
    methods: {
        initial_state() {
            return {
                test: null,
                scope_options: [],
                scope: null,
                test_options: [],
                test_uid: null,
                id: null,
                mode: 'create',
                errors: {},
                is_fetching: false,
            }
        },
        update_pickers() {
            $(this.$el).find('.selectpicker').selectpicker('redner').selectpicker('refresh')
        },
        async handle_fetch_scope() {
            const resp = await fetch(`${api_th_base_url}/scopes/${getSelectedProjectId()}?` +
                $.param({name: this.test})
            )
            if (resp.ok) {
                this.scope_options = await resp.json()
            } else {
                showNotify('ERROR', 'Error updating scope')
            }
        },
        async handle_change_test() {
            this.scope_options = []
            await this.handle_fetch_scope()
        },
        async handle_fetch_test_uid(){
            const resp = await fetch(`${api_th_base_url}/test_uid/${getSelectedProjectId()}/${this.test}/${this.scope}`)
            if (resp.ok) {
                this.test_uid = await resp.json()
                
            } else {
                showNotify('ERROR', 'Error updating scope')
            }
        },
        async handle_change_scope() {
            if (!this.scope_options.includes(this.scope)) {
                this.scope = undefined
            }
            this.test_uid = null
            await this.handle_fetch_test_uid()
        },

        async handle_create_threshold() {
            this.errors = {}
            const test_params = this.test_parameters.get()
            this.is_fetching = true
            const resp = await fetch(`${api_th_base_url}/thresholds/${getSelectedProjectId()}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({'test_uid': this.test_uid, 'params': test_params}),
            })
            if (resp.ok) {
                vueVm.registered_components[this.$props.thresholds_table_component_name]?.table_action('refresh')
                $(this.$el).modal('hide')
            } else {
                showNotify('ERROR', 'Error creating threshold')
                this.setError(await resp.json())
            }
            this.is_fetching = false
        },
        async handle_update_threshold() {
            this.errors = {}
            const test_params = this.test_parameters.get()
            this.is_fetching = true
            const resp = await fetch(`${api_th_base_url}/thresholds/${getSelectedProjectId()}/${this.id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({'test_uid': this.test_uid, 'params': test_params}),
            })
            if (resp.ok) {
                vueVm.registered_components[this.$props.thresholds_table_component_name]?.table_action('refresh')
                $(this.$el).modal('hide')
            } else {
                showNotify('ERROR', 'Error updating threshold')
                this.setError(await resp.json())
            }
            this.is_fetching = false
        },
        set(data, show = true) {
            this.clear()
            this.mode = 'update'
            paramsValues = data['params'].reduce((acc, curr)=>{
                acc[curr['name']] = {"comparison": curr['comparison'], "value": curr['value']}
                return acc
            },{})
            this.test_parameters.setValues(paramsValues)
            this.test_uid = data['test_uid']
            this.test = data['test_name']
            this.scope_options.push(data['test_scope'])
            this.scope = data['test_scope']
            this.id = data['id']
            show && $(this.$el).modal('show')
        },
        clear() {
            Object.assign(this.$data, this.initial_state())
            this.test_parameters.clearValues()
        },
        setError(errors) {
            errors.forEach(i => {
                if (i.loc[0] == "test_uid" && this.test===null){
                    this.errors['test'] = "this field is required"
                    this.errors['scope'] = "this field is required"
                }
                else if (i.loc[0] == "test_uid" && this.scope===null){
                    this.errors['scope'] = "this field is required"
                }
                else if (i.loc[0] == "params"){
                    this.test_parameters.setError(i)
                }
                else {
                    this.errors[i.loc[0]] = i.msg
                }
            })
        }
    }

}
register_component('ThresholdModal', ThresholdModal)


const threshold_delete = ids => {
    const url = `${api_th_base_url}/thresholds/${getSelectedProjectId()}?` + $.param({"id[]": ids})
    fetch(url, {
        method: 'DELETE'
    }).then(response => response.ok && vueVm.registered_components.table_thresholds?.table_action('refresh'))
}


var threshold_formatters = {
    actions(value, row, index) {
        return `
        <div class="d-flex justify-content-end">
            <button type="button" class="btn btn-24 btn-action action_edit"><i class="fas fa-cog"></i></button>
            <button type="button" class="btn btn-24 btn-action action_delete"><i class="fas fa-trash-alt"></i></button>
        </div>
        `
    },
    rules(value, row, index) {
        opsMap ={
            "gte": ">=",
            "lte": "<=",
            "lt": "<",
            "gt": ">",
            "eq": "==",
        }
        result = value.reduce((acc, curr) => `${acc} ${curr.name[0].toUpperCase()}${opsMap[curr.comparison]}${curr.value}`, '')
        return result
    },
    scopes(value, row, index) {
        return value.split("@")[1] || value
    },
    action_events: {
        'click .action_edit': function (e, value, row, index) {
            const component_proxy = vueVm.registered_components.threshold_modal
            component_proxy.set(row)
        },
        'click .action_delete': function (e, value, row, index) {
            threshold_delete(row.id)
        }
    }
}

$(() => {
    $('#delete_thresholds').on('click', () => {
        const table_proxy = vueVm.registered_components.table_thresholds
        const ids = table_proxy?.table_action('getSelections').map(i => i.id).join(',')
        ids && threshold_delete(ids) && table_proxy?.table_action('refresh')
    })
})