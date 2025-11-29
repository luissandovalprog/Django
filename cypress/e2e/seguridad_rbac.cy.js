describe('Seguridad y Roles (RBAC)', () => {

  beforeEach(() => {
    cy.viewport(1280, 720);
  });

  it('Escenario 1: El "Admin Sistema" NO debe tener acceso a datos clínicos', () => {
    // 1. Login como Administrador
    cy.visit('/accounts/login/');
    cy.get('input[name="username"]').type('adminsistema');
    cy.get('input[name="password"]').type('Hospital2025');
    cy.get('button[type="submit"]').click();

    // --- CORRECCIÓN CRÍTICA ---
    // Esperamos a que el login termine antes de navegar.
    // La señal de éxito es que la URL ya NO contiene "login".
    cy.url({ timeout: 20000 }).should('not.include', '/accounts/login/');

    // 2. Validar Acceso a su área (Auditoría)
    // Ahora que tenemos sesión segura, vamos explícitamente.
    cy.visit('/auditoria/historial/');
    
    // Validamos que cargue (esto confirma que tiene permisos de Admin)
    cy.contains('h3', 'Historial de Auditoría', { timeout: 10000 }).should('be.visible');
    
    // Verificar que ve la alerta de su rol (si está configurada en tu HTML)
    // Nota: Si cambiaste el nombre del rol, puede que este texto específico no aparezca,
    // pero la prueba del H3 arriba ya confirma el acceso.
    cy.get('.alert-warning').should('be.visible'); 

    // 3. INTENTO DE INTRUSIÓN: Tratar de entrar al dashboard clínico
    cy.visit('/sistema/dashboard/');

    // 4. Validar que NO se muestra información sensible
    // El Admin entra al dashboard, pero NO debe ver las tablas clínicas
    cy.get('.dashboard-container').should('be.visible');
    
    // Las tablas de pacientes NO deben existir para él
    cy.contains('Recién Nacidos Hospitalizados').should('not.exist');
    cy.contains('Madres sin Parto').should('not.exist');
  });

  it('Escenario 2: La "Matrona" NO debe tener acceso a la Auditoría', () => {
    // 1. Login como Matrona
    cy.visit('/accounts/login/');
    cy.get('input[name="username"]').type('matrona1');
    cy.get('input[name="password"]').type('Hospital2025');
    cy.get('button[type="submit"]').click();

    // Asegurar login exitoso esperando al dashboard
    cy.get('.dashboard-container', { timeout: 10000 }).should('be.visible');

    // 2. INTENTO DE INTRUSIÓN: Tratar de entrar a auditoría
    cy.visit('/auditoria/historial/');

    // 3. Validar RECHAZO (Redirección al dashboard)
    // Si la matrona intenta entrar, el sistema la debe devolver al dashboard
    cy.url().should('include', '/sistema/dashboard/');
    
    // Validar mensaje de error (Toast)
    cy.contains(/no tiene permisos/i).should('be.visible');
  });

});