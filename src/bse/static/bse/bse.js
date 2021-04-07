const app = new Vue({
  el: '#app',
  data: {
    filter: '',
    rows: [
      { department: 'Accounting', employees: ['Bradley', 'Jones', 'Alvarado'] },
      {
        department: 'Human Resources',
        employees: ['Juarez', 'Banks', 'Smith'],
      },
      {
        department: 'Production',
        employees: ['Sweeney', 'Bartlett', 'Singh'],
      },
      {
        department: 'Research and Development',
        employees: ['Lambert', 'Williamson', 'Smith'],
      },
      {
        department: 'Sales and Marketing',
        employees: ['Prince', 'Townsend', 'Jones'],
      },
    ],
  },
  methods: {
    highlightMatches(text) {
      const matchExists = text.toLowerCase().includes(this.filter.toLowerCase());
      if (!matchExists) return text;

      const re = new RegExp(this.filter, 'ig');
      return text.replace(re, (matchedText) => `<strong>${matchedText}</strong>`);
    },
  },
  computed: {
    filteredRows() {
      return this.rows.filter((row) => {
        const employees = row.employees.toString().toLowerCase();
        const department = row.department.toLowerCase();
        const searchTerm = this.filter.toLowerCase();

        return department.includes(searchTerm) || employees.includes(searchTerm);
      });
    },
  },
});
