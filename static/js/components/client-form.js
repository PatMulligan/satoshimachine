window.app.component('client-form', {
  name: 'ClientForm',
  template: '#client-form',
  
  props: {
    client: {
      type: Object,
      default: () => ({
        name: '',
        wallet_id: '',
        dca_percentage: 0,
        commission_percentage: 0,
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
        dca_percentage: 0,
        commission_percentage: 0,
        active: true
      }
    }
  },
  
  watch: {
    client: {
      handler(newClient) {
        this.form = { ...newClient }
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