describe('Gestión de Pacientes (Madres)', () => {
  
  beforeEach(() => {
    cy.visit('/accounts/login/');
    cy.get('input[name="username"]').type('matrona1');
    cy.get('input[name="password"]').type('Hospital2025');
    cy.get('button[type="submit"]').click();
    cy.contains('Sistema de Gestión Neonatal', { timeout: 10000 }).should('be.visible');
  });

  it('Debe registrar una nueva madre exitosamente y aparecer en el dashboard', () => {
    cy.visit('/sistema/madre/crear/');

    // Usamos Date.now() para que el RUT sea SIEMPRE único (evita error de duplicados)
    const uniqueId = Date.now().toString().slice(-3); 
    const nombreMadre = `Valentina Test ${uniqueId}`;

    // Llenar TODOS los campos posibles
    cy.get('input[name="rut"]').type(`15.111.${uniqueId}-k`); 
    cy.get('input[name="nombre"]').type(nombreMadre);
    cy.get('input[name="fecha_nacimiento"]').type('1995-05-20');
    
    // El campo que crees que falta
    cy.get('input[name="telefono"]').type('+56912345678'); 
    
    cy.get('select[name="nacionalidad"]').select('Chilena');
    cy.get('select[name="prevision"]').select('FONASA');
    cy.get('input[name="direccion"]').type('Av. Argentina 123, Chillán');
    cy.get('textarea[name="antecedentes_medicos"]').type('Paciente de prueba Cypress');

    cy.get('button[type="submit"]').click();

    // --- BLOQUE DE DEPURACIÓN ---
    // Si falla la redirección, esto nos imprimirá el error en la consola de Cypress
    cy.get('body').then(($body) => {
        // Busca textos de error comunes de Django
        const errorList = $body.find('.errorlist, .invalid-feedback, .alert-danger');
        if (errorList.length > 0) {
            cy.log('🔴 ERROR DE VALIDACIÓN ENCONTRADO: ' + errorList.text());
        }
    });
    // ---------------------------

    cy.contains('td', nombreMadre, { timeout: 15000 }).should('be.visible');

    // 2. Ahora que ya estamos seguros de estar en el dashboard, verificamos la URL
    cy.url().should('include', '/sistema/dashboard/');
  });
});