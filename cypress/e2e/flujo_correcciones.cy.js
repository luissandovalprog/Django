describe('Flujo Colaborativo: Correcciones y Notificaciones', () => {

  beforeEach(() => {
    cy.viewport(1280, 720);
  });

  it('El Médico corrige una madre existente y la Matrona recibe la notificación', () => {
    
    // ============================================================
    // ROL 1: MÉDICO (Entra directo a corregir)
    // ============================================================
    cy.log('👨‍⚕️ PASO 1: Médico busca paciente y corrige');
    
    cy.visit('/accounts/login/');
    cy.get('input[name="username"]').type('medico1'); 
    cy.get('input[name="password"]').type('Hospital2025');
    cy.get('button[type="submit"]').click();
    
    cy.get('.dashboard-container', { timeout: 20000 }).should('be.visible');

    // ESTRATEGIA CORREGIDA: Buscar específicamente en la tabla de MADRES
    cy.contains('.card', 'Madres sin Parto')
      .find('tbody tr')
      .first()
      .then(($row) => {
        const nombrePaciente = $row.find('td').eq(0).text().trim();
        cy.log('📌 Corrigiendo a: ' + nombrePaciente);
        Cypress.env('paciente_corregida', nombrePaciente);

        cy.wrap($row)
          .find('a.btn-warning')
          .should('be.visible')
          .click();
      });

    // Llenar Formulario de Corrección
    cy.contains('h2', 'Anexar Corrección', { timeout: 10000 }).should('be.visible');
    
    cy.get('select[name="campo_corregido"]').select('Previsión');
    
    cy.get('input[name="valor_original"]', { timeout: 10000 })
      .should('not.have.value', 'Cargando...')
      .and('not.have.value', ''); 

    cy.get('input[name="valor_nuevo"]').type('ISAPRE');
    cy.get('textarea[name="justificacion"]').type('Corrección administrativa solicitada por auditoría.');

    cy.get('button[type="submit"]').click();

    cy.contains('Corrección anexada').should('be.visible');
    cy.contains('Cerrar Sesión').click();


    // ============================================================
    // ROL 2: MATRONA (Verifica la notificación)
    // ============================================================
    cy.then(() => {
      cy.log('🔔 PASO 2: Matrona verifica buzón');
      
      cy.visit('/accounts/login/');
      cy.get('input[name="username"]').type('matrona1');
      cy.get('input[name="password"]').type('Hospital2025');
      cy.get('button[type="submit"]').click();

      cy.get('.dashboard-container', { timeout: 20000 }).should('be.visible');
      
      // 1. Verificar el Badge Rojo
      cy.get('#notifications-badge', { timeout: 10000 }).should('exist');
      
      // --- TRUCO NINJA AQUÍ ---
      // Borramos el mensaje de "Bienvenido" que tapa el menú
      // Si no hacemos esto, Cypress falla diciendo que el elemento está "covered"
      cy.get('body').then(($body) => {
        if ($body.find('.messages-container').length > 0) {
            cy.get('.messages-container').invoke('remove');
        }
      });

      // 2. Abrir notificaciones
      cy.get('#notifications-bell').click();
      
      // 3. Verificar que la notificación existe
      cy.get('#notifications-list').should('be.visible');
      // Le damos un poco de espera extra por si la animación del dropdown tarda
      cy.contains('Corrección anexada', { timeout: 5000 }).should('be.visible');
    });
  });
});