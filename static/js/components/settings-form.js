window.app.component('settings-form', {
  name: 'SettingsForm',
  template: '#settings-form',
  
  props: {
    config: {
      type: Object,
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  
  data() {
    return {
      form: {
        processing_enabled: false,
        lamassu_server_ip: '',
        fixed_mode_schedule: 'daily',
        fixed_mode_time: '00:00',
        max_daily_fixed_amount: 0
      },
      scheduleOptions: [
        { label: 'Daily', value: 'daily' },
        { label: 'Weekly', value: 'weekly' },
        { label: 'Monthly', value: 'monthly' }
      ]
    }
  },
  
  watch: {
    config: {
      handler(newConfig) {
        this.form = { ...newConfig }
      },
      immediate: true
    }
  },
  
  methods: {
    async onSubmit() {
      try {
        await this.$refs.form.validate()
        this.$emit('save', this.form)
      } catch (error) {
        // Form validation failed
      }
    }
  }
}) 