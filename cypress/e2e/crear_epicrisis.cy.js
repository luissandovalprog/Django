describe('Flujo Clínico: Epicrisis e Indicaciones al Alta', () => {

  beforeEach(() => {
    cy.viewport(1280, 720);
    
    // 1. LOGIN CORRECTO (Como Médico)
    cy.visit('/accounts/login/');
    cy.get('input[name="username"]').type('medico1'); 
    cy.get('input[name="password"]').type('Hospital2025');
    cy.get('button[type="submit"]').click();
    
    cy.get('.dashboard-container', { timeout: 20000 }).should('be.visible');
  });

  it('Debe completar una epicrisis y agregar indicaciones médicas dinámicas', () => {
    // 2. NAVEGAR A LA LISTA DE EPICRISIS
    cy.visit('/sistema/epicrisis/');
    cy.contains('h2', 'Gestión de Epicrisis').should('be.visible');

    // 3. SELECCIONAR UN PACIENTE PENDIENTE
    cy.get('a.btn-success')
      .should('have.length.at.least', 1, 'Debe haber al menos un paciente pendiente')
      .first()
      .click();

    // 4. VALIDAR CARGA
    cy.contains('h2', 'Crear Epicrisis', { timeout: 10000 }).should('be.visible');
    
    // 5. LLENAR DATOS CLÍNICOS
    cy.log('📝 Llenando resumen clínico...');
    cy.get('input[name="motivo_ingreso"]').type('Trabajo de parto activo');
    cy.get('textarea[name="resumen_evolucion"]').type('Evolución fisiológica sin complicaciones.');
    cy.get('textarea[name="diagnostico_egreso"]').type('Puerperio Fisiológico.');
    
    cy.get('select[name="condicion_egreso"]').select('Buena');
    cy.get('input[name="control_posterior"]').type('En 7 días');
    cy.get('textarea[name="indicaciones_alta"]').type('Lactancia materna exclusiva.');

    // 6. PRUEBA DE JAVASCRIPT: AGREGAR INDICACIONES
    cy.log('💊 Agregando medicamentos dinámicamente...');
    
    // --- Indicación 1: Medicamento ---
    cy.get('#new-tipo').select('Medicamento');
    cy.get('#new-descripcion').type('Paracetamol');
    cy.get('#new-dosis').type('500mg');
    cy.get('#new-frecuencia').type('Cada 8 horas SOS');
    cy.get('#new-via').type('Oral');
    
    cy.get('#btn-agregar-indicacion').click();

    // --- CORRECCIÓN AQUÍ ---
    // Buscamos el texto exacto "Paracetamol" (no en mayúsculas)
    // Y verificamos que el tipo "MEDICAMENTO" sí esté en mayúsculas (tu JS lo hace así)
    cy.get('#indicaciones-container').should('contain', 'Paracetamol');
    cy.get('#indicaciones-container').should('contain', 'MEDICAMENTO');
    cy.get('#indicaciones-container').should('contain', '500mg');

    // --- Indicación 2: Cuidado ---
    cy.get('#new-tipo').select('Cuidado de Enfermería');
    cy.get('#new-descripcion').type('Aseo zona operatoria');
    cy.get('#new-frecuencia').type('Diario');
    cy.get('#new-dosis').clear(); 
    cy.get('#new-via').clear();
    
    cy.get('#btn-agregar-indicacion').click();
    
    // Verificar conteo (deben haber 2 divs hijos directos en la lista)
    cy.get('#indicaciones-container').children().should('have.length', 2);

    // 7. GUARDAR
    cy.get('button[type="submit"]').click();

    // 8. VERIFICAR ÉXITO
    // Esperamos redirección a la lista
    cy.url().should('include', '/sistema/epicrisis/');
    // Mensaje de éxito
    cy.contains('guardadas exitosamente').should('be.visible');
  });
});