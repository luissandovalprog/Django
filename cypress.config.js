const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    // Agrega esta línea para definir la URL base de tu servidor Django
    baseUrl: 'http://127.0.0.1:8000', 
    
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
  },
});