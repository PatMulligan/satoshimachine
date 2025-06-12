window.app = Vue.createApp({
  el: '#vue',
  mixins: [windowMixin],
  
  data() {
    return {
      loading: false,
      testing: false,
      config: {
        processing_enabled: false,
        lamassu_server_ip: '',
        fixed_mode_schedule: 'daily',
        fixed_mode_time: '00:00',
        max_daily_fixed_amount: 0
      }
    }
  },

  methods: {
    async loadConfig() {
      try {
        const {data} = await LNbits.api.request(
          'GET',
          '/dca_admin/api/v1/config',
          this.g.user.wallets[0].inkey
        )
        this.config = data
      } catch (error) {
        LNbits.utils.notifyApiError(error)
      }
    },

    async saveConfig(config) {
      this.loading = true
      try {
        await LNbits.api.request(
          'PUT',
          '/dca_admin/api/v1/config',
          this.g.user.wallets[0].inkey,
          config
        )
        this.$q.notify({
          type: 'positive',
          message: 'Configuration saved successfully',
          timeout: 5000
        })
        await this.loadConfig()
      } catch (error) {
        LNbits.utils.notifyApiError(error)
      } finally {
        this.loading = false
      }
    },

    async testConnection() {
      this.testing = true
      try {
        await LNbits.api.request(
          'POST',
          '/dca_admin/api/v1/test-connection',
          this.g.user.wallets[0].inkey,
          { server_ip: this.config.lamassu_server_ip }
        )
        this.$q.notify({
          type: 'positive',
          message: 'Connection test successful',
          timeout: 5000
        })
      } catch (error) {
        LNbits.utils.notifyApiError(error)
      } finally {
        this.testing = false
      }
    }
  },

  created() {
    this.loadConfig()
  }
}) 