describe('Sistema de Autenticación Hospital', () => {
  it('Debe permitir el ingreso a una Matrona y redirigir al dashboard', () => {
    // 1. Cargar página
    cy.visit('/accounts/login/');

    // 2. Llenar formulario
    cy.get('input[name="username"]').type('matrona1');
    cy.get('input[name="password"]').type('Hospital2025');
    
    // 3. Enviar
    cy.get('button[type="submit"]').click();

    // --- CAMBIO IMPORTANTE AQUÍ ---
    
    // 4. Validación Visual (Esto obliga a Cypress a esperar la carga)
    // Buscamos el texto del encabezado azul que se ve en tu imagen
    cy.contains('Sistema de Gestión Neonatal', { timeout: 10000 }).should('be.visible');

    // 5. Validación de URL
    // Ahora que ya vimos el título, la URL está garantizada de ser la correcta
    cy.url().should('include', '/sistema/dashboard/');
  });
});