describe('Módulo de Reportes y Estadísticas', () => {

  beforeEach(() => {
    cy.viewport(1280, 720);
    
    // 1. LOGIN COMO SUPERVISOR
    // Usamos al supervisor porque tiene permisos totales sobre reportes
    cy.visit('/accounts/login/');
    cy.get('input[name="username"]').type('supervisor');
    cy.get('input[name="password"]').type('1234');
    cy.get('button[type="submit"]').click();
    
    // Esperar carga
    cy.get('.dashboard-container', { timeout: 20000 }).should('be.visible');
  });

  it('Debe generar y descargar el reporte REM (PDF)', () => {
    // 2. NAVEGAR A REPORTES
    cy.visit('/reportes/');
    cy.contains('h2', 'Generación de Reportes').should('be.visible');

    // 3. SELECCIONAR REPORTE REM
    // Buscamos el enlace y hacemos click
    cy.contains('a', 'Generar REM').click();
    
    // Validar que estamos en el formulario correcto
    cy.contains('h2', 'Generar Reporte REM Neonatal').should('be.visible');

    // 4. LLENAR FECHAS
    // Seleccionamos un rango amplio para asegurar datos
    cy.get('input[name="fecha_inicio"]').type('2025-01-01');
    cy.get('input[name="fecha_fin"]').type('2025-12-31');

    // 5. PREPARAR LA INTERCEPCIÓN
    // Antes de hacer clic, le decimos a Cypress: "Espía la petición POST que va a /rem-bs22/"
    cy.intercept('POST', '**/reportes/rem-bs22/').as('descargaPDF');

    // 6. GENERAR
    cy.get('button[type="submit"]').click();

    // 7. VALIDAR LA DESCARGA (Sin abrir el archivo)
    // Esperamos a que el servidor responda y verificamos los encabezados
    cy.wait('@descargaPDF').then((interception) => {
      // El servidor debe responder OK
      expect(interception.response.statusCode).to.eq(200);
      
      // El tipo de contenido DEBE ser PDF
      expect(interception.response.headers['content-type']).to.contain('application/pdf');
      
      // Debe venir como adjunto (attachment)
      expect(interception.response.headers['content-disposition']).to.contain('attachment');
      expect(interception.response.headers['content-disposition']).to.contain('filename="REM_BS22_');
    });
  });

  it('Debe exportar la base de datos a Excel', () => {
    // 1. IR DIRECTO AL FORMULARIO DE EXCEL
    cy.visit('/reportes/exportar-excel/');
    cy.contains('h2', 'Exportar Datos a Excel').should('be.visible');

    // 2. LLENAR FECHAS
    cy.get('input[name="fecha_inicio"]').type('2025-01-01');
    cy.get('input[name="fecha_fin"]').type('2025-12-31');

    // 3. PREPARAR INTERCEPCIÓN
    // Espiamos la URL de exportación
    cy.intercept('POST', '**/reportes/exportar-excel/').as('descargaExcel');

    // 4. EXPORTAR
    cy.get('button[type="submit"]').click();

    // 5. VALIDAR
    cy.wait('@descargaExcel').then((interception) => {
      expect(interception.response.statusCode).to.eq(200);
      
      // El tipo de contenido DEBE ser Excel
      // A veces Django lo envía como octet-stream o el mime type de excel
      const contentType = interception.response.headers['content-type'];
      expect(contentType).to.satisfy((msg) => {
        return msg.includes('spreadsheetml') || msg.includes('ms-excel');
      });
      
      expect(interception.response.headers['content-disposition']).to.contain('filename="partos_');
    });
  });

});