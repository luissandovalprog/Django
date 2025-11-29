describe('Trazabilidad: Auditoría del Sistema', () => {

  beforeEach(() => {
    cy.viewport(1280, 720);
  });

  it('El Administrador debe poder ver y filtrar los logs de las acciones recientes', () => {
    // 1. LOGIN COMO ADMIN SISTEMA
    cy.visit('/accounts/login/');
    cy.get('input[name="username"]').type('adminsistema');
    cy.get('input[name="password"]').type('Hospital2025');
    cy.get('button[type="submit"]').click();

    // --- CORRECCIÓN DE ESTABILIDAD ---
    // 1. Esperar a que el login termine (URL ya no es login)
    cy.url({ timeout: 20000 }).should('not.include', '/accounts/login/');

    // 2. Navegar explícitamente a Auditoría
    // (Esto evita fallos si la redirección automática no está configurada o falla)
    cy.visit('/auditoria/historial/');
    
    // 3. Validar que estamos en Auditoría
    cy.contains('h3', 'Historial de Auditoría', { timeout: 10000 }).should('be.visible');

    // 4. VERIFICAR QUE EXISTEN LOGS
    // Buscamos filas en la tabla. Como corrimos tests antes, debe haber datos.
    cy.get('tbody tr').should('have.length.at.least', 1);

    // 5. FILTRAR POR USUARIO (Matrona)
    cy.log('🔍 Buscando trazas de la matrona...');
    
    // Usamos el select para filtrar.
    cy.get('select[name="usuario"]').should('be.visible').select('matrona1'); 
    cy.get('button[type="submit"]').click();

    // 6. VALIDAR RESULTADOS DEL FILTRO
    // Esperar recarga de URL
    cy.url().should('include', 'usuario=matrona1');
    
    // Verificar que en la tabla aparezca el usuario filtrado
    cy.get('tbody').should('contain', 'matrona1');

    // 7. VALIDAR DETALLES DE SEGURIDAD (Columnas)
    // Validamos la primera fila para asegurar que guarda datos técnicos
    cy.get('tbody tr').first().within(() => {
      // Columna 2: Acción (ej: LOGIN)
      cy.get('td').eq(2).should('not.be.empty'); 
      // Columna 4: IP (Trazabilidad)
      cy.get('td').eq(4).should('not.be.empty'); 
    });

    // 8. LIMPIAR FILTROS
    cy.contains('a', 'Limpiar').click();
    cy.url().should('not.include', 'usuario=matrona1');
  });
});