window.app.component('commission-recipient-form', {
  name: 'CommissionRecipientForm',
  template: '#commission-recipient-form',
  
  props: {
    recipient: {
      type: Object,
      default: () => ({
        name: '',
        wallet_id: '',
        percentage: 0,
        active: true
      })
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  
  data() {
    return {
      form: {
        name: '',
        wallet_id: '',
        percentage: 0,
        active: true
      }
    }
  },
  
  watch: {
    recipient: {
      handler(newRecipient) {
        this.form = { ...newRecipient }
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