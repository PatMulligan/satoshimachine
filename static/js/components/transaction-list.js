window.app.component('transaction-list', {
  name: 'TransactionList',
  template: '#transaction-list',
  
  props: {
    transactions: {
      type: Array,
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  
  data() {
    return {
      pagination: {
        sortBy: 'created_at',
        descending: true,
        page: 1,
        rowsPerPage: 10
      },
      columns: [
        {
          name: 'id',
          label: 'ID',
          field: 'id',
          align: 'left'
        },
        {
          name: 'client_name',
          label: 'Client',
          field: 'client_name',
          align: 'left'
        },
        {
          name: 'amount',
          label: 'Amount',
          field: 'amount',
          align: 'right'
        },
        {
          name: 'status',
          label: 'Status',
          field: 'status',
          align: 'center'
        },
        {
          name: 'created_at',
          label: 'Created',
          field: 'created_at',
          align: 'left',
          format: val => new Date(val).toLocaleString()
        },
        {
          name: 'actions',
          label: 'Actions',
          field: 'actions',
          align: 'center'
        }
      ]
    }
  },
  
  methods: {
    getStatusColor(status) {
      const colors = {
        pending: 'warning',
        approved: 'positive',
        rejected: 'negative',
        completed: 'positive',
        failed: 'negative'
      }
      return colors[status] || 'grey'
    },
    
    formatAmount(amount) {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'GTQ'
      }).format(amount)
    }
  }
}) 