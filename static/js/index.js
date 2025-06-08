window.app = Vue.createApp({
  el: '#vue',
  mixins: [windowMixin],
  delimiters: ['${', '}'],
  data: function () {
    return {
      invoiceAmount: 10,
      qrValue: 'lnurlpay',
      myex: [],
      myexTable: {
        columns: [
          {name: 'id', align: 'left', label: 'ID', field: 'id'},
          {name: 'name', align: 'left', label: 'Name', field: 'name'},
          {
            name: 'wallet',
            align: 'left',
            label: 'Wallet',
            field: 'wallet'
          },
          {
            name: 'total',
            align: 'left',
            label: 'Total sent/received',
            field: 'total'
          }
        ],
        pagination: {
          rowsPerPage: 10
        }
      },
      formDialog: {
        show: false,
        data: {},
        advanced: {}
      },
      urlDialog: {
        show: false,
        data: {}
      }
    }
  },

  ///////////////////////////////////////////////////
  ////////////////METHODS FUNCTIONS//////////////////
  ///////////////////////////////////////////////////

  methods: {
    async closeFormDialog() {
      this.formDialog.show = false
      this.formDialog.data = {}
    },
    async getSatoshiMachines() {
      await LNbits.api
        .request(
          'GET',
          '/satoshimachine/api/v1/myex',
          this.g.user.wallets[0].inkey
        )
        .then(response => {
          this.myex = response.data
        })
        .catch(err => {
          LNbits.utils.notifyApiError(err)
        })
    },
    async sendSatoshiMachineData() {
      const data = {
        name: this.formDialog.data.name,
        lnurlwithdrawamount: this.formDialog.data.lnurlwithdrawamount,
        lnurlpayamount: this.formDialog.data.lnurlpayamount
      }
      const wallet = _.findWhere(this.g.user.wallets, {
        id: this.formDialog.data.wallet
      })
      if (this.formDialog.data.id) {
        data.id = this.formDialog.data.id
        data.total = this.formDialog.data.total
        await this.updateSatoshiMachine(wallet, data)
      } else {
        await this.createSatoshiMachine(wallet, data)
      }
    },

    async updateSatoshiMachineForm(tempId) {
      const satoshimachine = _.findWhere(this.myex, {id: tempId})
      this.formDialog.data = {
        ...satoshimachine
      }
      if (this.formDialog.data.tip_wallet != '') {
        this.formDialog.advanced.tips = true
      }
      if (this.formDialog.data.withdrawlimit >= 1) {
        this.formDialog.advanced.otc = true
      }
      this.formDialog.show = true
    },
    async createSatoshiMachine(wallet, data) {
      data.wallet = wallet.id
      await LNbits.api
        .request('POST', '/satoshimachine/api/v1/myex', wallet.adminkey, data)
        .then(response => {
          this.myex.push(response.data)
          this.closeFormDialog()
        })
        .catch(error => {
          LNbits.utils.notifyApiError(error)
        })
    },

    async updateSatoshiMachine(wallet, data) {
      data.wallet = wallet.id
      await LNbits.api
        .request(
          'PUT',
          `/satoshimachine/api/v1/myex/${data.id}`,
          wallet.adminkey,
          data
        )
        .then(response => {
          this.myex = _.reject(this.myex, obj => obj.id == data.id)
          this.myex.push(response.data)
          this.closeFormDialog()
        })
        .catch(error => {
          LNbits.utils.notifyApiError(error)
        })
    },
    async deleteSatoshiMachine(tempId) {
      var satoshimachine = _.findWhere(this.myex, {id: tempId})
      const wallet = _.findWhere(this.g.user.wallets, {
        id: satoshimachine.wallet
      })
      await LNbits.utils
        .confirmDialog('Are you sure you want to delete this SatoshiMachine?')
        .onOk(function () {
          LNbits.api
            .request(
              'DELETE',
              '/satoshimachine/api/v1/myex/' + tempId,
              wallet.adminkey
            )
            .then(() => {
              this.myex = _.reject(this.myex, function (obj) {
                return obj.id === satoshimachine.id
              })
            })
            .catch(error => {
              LNbits.utils.notifyApiError(error)
            })
        })
    },

    async exportCSV() {
      await LNbits.utils.exportCSV(this.myexTable.columns, this.myex)
    },
    async itemsArray(tempId) {
      const satoshimachine = _.findWhere(this.myex, {id: tempId})
      return [...satoshimachine.itemsMap.values()]
    },
    async openformDialog(id) {
      const [tempId, itemId] = id.split(':')
      const satoshimachine = _.findWhere(this.myex, {id: tempId})
      if (itemId) {
        const item = satoshimachine.itemsMap.get(id)
        this.formDialog.data = {
          ...item,
          satoshimachine: tempId
        }
      } else {
        this.formDialog.data.satoshimachine = tempId
      }
      this.formDialog.data.currency = satoshimachine.currency
      this.formDialog.show = true
    },
    async openUrlDialog(tempid) {
      this.urlDialog.data = _.findWhere(this.myex, {id: tempid})
      this.qrValue = this.urlDialog.data.lnurlpay

      // Connecting to our websocket fired in tasks.py
      this.connectWebocket(this.urlDialog.data.id)

      this.urlDialog.show = true
    },
    async closeformDialog() {
      this.formDialog.show = false
      this.formDialog.data = {}
    },
    async createInvoice(tempid) {
      ///////////////////////////////////////////////////
      ///Simple call to the api to create an invoice/////
      ///////////////////////////////////////////////////
      myex = _.findWhere(this.myex, {id: tempid})
      const wallet = _.findWhere(this.g.user.wallets, {id: myex.wallet})
      const data = {
        satoshimachine_id: tempid,
        amount: this.invoiceAmount,
        memo: 'SatoshiMachine - ' + myex.name
      }
      await LNbits.api
        .request('POST', `/satoshimachine/api/v1/myex/payment`, wallet.inkey, data)
        .then(response => {
          this.qrValue = response.data.payment_request
          this.connectWebocket(wallet.inkey)
        })
        .catch(error => {
          LNbits.utils.notifyApiError(error)
        })
    },
    connectWebocket(satoshimachine_id) {
      //////////////////////////////////////////////////
      ///wait for pay action to happen and do a thing////
      ///////////////////////////////////////////////////
      if (location.protocol !== 'http:') {
        localUrl =
          'wss://' +
          document.domain +
          ':' +
          location.port +
          '/api/v1/ws/' +
          satoshimachine_id
      } else {
        localUrl =
          'ws://' +
          document.domain +
          ':' +
          location.port +
          '/api/v1/ws/' +
          satoshimachine_id
      }
      this.connection = new WebSocket(localUrl)
      this.connection.onmessage = () => {
        this.urlDialog.show = false
      }
    }
  },
  ///////////////////////////////////////////////////
  //////LIFECYCLE FUNCTIONS RUNNING ON PAGE LOAD/////
  ///////////////////////////////////////////////////
  async created() {
    await this.getSatoshiMachines()
  }
})
