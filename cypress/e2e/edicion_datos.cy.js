describe('Gestión de Calidad: Edición de Datos Clínicos (Matrona)', () => {

  beforeEach(() => {
    cy.viewport(1280, 720);
  });

  it('La Matrona debe poder corregir el peso de un Recién Nacido existente', () => {
    // 1. LOGIN COMO MATRONA
    cy.visit('/accounts/login/');
    cy.get('input[name="username"]').type('matrona1');
    cy.get('input[name="password"]').type('Hospital2025');
    cy.get('button[type="submit"]').click();
    
    // Esperar carga del dashboard
    cy.get('.dashboard-container', { timeout: 20000 }).should('be.visible');

    // 2. SELECCIONAR UN PARTO EXISTENTE DESDE EL DASHBOARD
    // Buscamos en la tabla de "Recién Nacidos Hospitalizados" (la de arriba)
    cy.contains('h2', 'Recién Nacidos Hospitalizados').should('be.visible');
    
    // Hacemos clic en el botón "Ver detalle" (Ojo / Azul) de la PRIMERA fila disponible
    cy.get('table').first()
      .find('tbody tr').first()
      .find('a.btn-icon') // Busca los botones de acción
      .first() // El primero suele ser "Ver Detalle" (Azul)
      .click();

    // 3. ENTRAR AL DETALLE
    cy.contains('h2', 'Detalle del Parto', { timeout: 10000 }).should('be.visible');

    // 4. BUSCAR EL RN Y EDITAR
    // En la vista de detalle, buscamos la sección de Recién Nacidos
    // y hacemos clic en el botón de editar (Lápiz / Amarillo)
    cy.contains('h3', 'Recién Nacidos')
      .parents('.card') // Subimos al contenedor de la tarjeta
      .find('table tbody tr').first() // Buscamos la primera fila de RNs
      .find('a.btn-icon') // Botón de editar
      .click();

    // 5. FORMULARIO DE EDICIÓN
    // Validamos que cargó el formulario
    cy.get('form').should('be.visible');
    
    // Modificamos el peso (Usamos un valor distintivo para verificar después)
    const nuevoPeso = '3950';
    
    cy.get('input[name="peso_gramos"]')
      .should('be.visible')
      .clear()
      .type(nuevoPeso);

    cy.get('button[type="submit"]').click();

    // 6. VALIDAR RESULTADO
    // Esperamos volver al detalle del parto
    cy.contains('h2', 'Detalle del Parto', { timeout: 10000 }).should('be.visible');
    
    // Verificamos el mensaje de éxito
    cy.contains('Recién nacido actualizado exitosamente').should('be.visible');
    
    // Verificamos que el nuevo peso aparece en la tabla
    cy.contains(nuevoPeso).should('be.visible');
  });

});