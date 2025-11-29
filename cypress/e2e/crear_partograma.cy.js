describe('Flujo Clínico: Crear Partograma a Paciente Existente', () => {

  // Configuración de pantalla
  beforeEach(() => {
    cy.viewport(1280, 720);
    
    // 1. LOGIN
    cy.visit('/accounts/login/');
    cy.get('input[name="username"]').type('matrona1');
    cy.get('input[name="password"]').type('Hospital2025');
    cy.get('button[type="submit"]').click();
    
    // Esperar a que cargue el dashboard
    cy.get('.dashboard-container', { timeout: 10000 }).should('be.visible');
  });

  it('Encuentra la primera paciente pendiente en la lista y crea su partograma', () => {
    // 2. Ir a la lista de partogramas
    cy.visit('/sistema/partogramas/');
    cy.contains('h2', 'Gestión de Partogramas').should('be.visible');

    // 3. SELECCIONAR LA PRIMERA DISPONIBLE
    // Buscamos todos los botones verdes ("Crear Partograma") y hacemos clic en el PRIMERO (first)
    // Esto tomará a la primera madre de tu lista que necesite partograma.
    cy.get('a.btn-success')
      .should('have.length.at.least', 1) // Validar que exista al menos una paciente pendiente
      .first()
      .click();

    // 4. LLENAR EL FORMULARIO
    cy.log('📝 Llenando formulario para la paciente seleccionada...');
    cy.contains('h2', 'Crear Partograma', { timeout: 10000 }).should('be.visible');

    // Datos obligatorios y validación de formato
    cy.get('input[name="hora_inicio"]').type('08:30');
    
    // Dilatación (formato hora-valor)
    cy.get('input[name="dilatacion_cm"]').type('8-4, 9-5, 10-6');
    
    // Resto de datos clínicos
    cy.get('input[name="fcf_latidos"]').type('140-145');
    cy.get('input[name="contracciones"]').type('3-4'); 
    cy.get('input[name="presion_arterial"]').type('120/80');
    cy.get('textarea[name="observaciones_clinicas"]').type('Registro automático sobre paciente existente.');

    // 5. GUARDAR
    cy.get('button[type="submit"]').click();

    // 6. VERIFICAR ÉXITO
    // Esperamos el mensaje de éxito o la redirección al detalle
    cy.contains('Partograma registrado exitosamente', { timeout: 10000 }).should('be.visible');
  });
});