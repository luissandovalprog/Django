describe('Flujo Clínico: Registro de Parto y Recién Nacido', () => {
  
  const uniqueId = Date.now().toString().slice(-3);
  const nombreMadre = `Madre Parto ${uniqueId}`;
  const rutMadre = `9.222.${uniqueId}-k`;

  beforeEach(() => {
    cy.visit('/accounts/login/');
    cy.get('input[name="username"]').type('matrona1');
    cy.get('input[name="password"]').type('Hospital2025');
    cy.get('button[type="submit"]').click();
    
    // Asegurar carga completa del dashboard
    cy.url({ timeout: 20000 }).should('include', '/sistema/dashboard/');
    cy.get('.dashboard-container', { timeout: 10000 }).should('be.visible');
  });

  it('Debe registrar una madre y luego su parto completo con recién nacido', () => {
    // --- FASE 1: CREAR MADRE ---
    cy.log('📌 FASE 1: Creando Madre');
    cy.visit('/sistema/madre/crear/');
    
    cy.get('input[name="rut"]').type(rutMadre); 
    cy.get('input[name="nombre"]').type(nombreMadre);
    cy.get('input[name="fecha_nacimiento"]').type('1998-01-15');
    cy.get('input[name="telefono"]').type('+56987654321'); 
    cy.get('input[name="direccion"]').type('Calle Prueba 123, Chillán');
    cy.get('textarea[name="antecedentes_medicos"]').type('Sin antecedentes');
    cy.get('select[name="nacionalidad"]').select('Chilena');
    cy.get('select[name="prevision"]').select('FONASA');
    
    cy.get('button[type="submit"]').click();
    
    
    // --- FASE 2: NAVEGACIÓN (Estrategia Híbrida) ---
    cy.log('📌 FASE 2: Obteniendo URL del paciente...');
    
    // Usar el buscador para aislar la fila
    cy.url({ timeout: 20000 }).should('include', '/sistema/dashboard/');
    cy.get('input[name="busqueda"]').should('be.visible').clear().type(nombreMadre + '{enter}');
    
    // Esperar recarga
    cy.url().should('include', 'busqueda=');
    
    // AQUÍ ESTÁ EL TRUCO: Extraer href y navegar
    // 1. Buscar la celda con el nombre
    // 2. Subir a la fila (parents tr)
    // 3. Bajar al botón (find a)
    // 4. Obtener el atributo href y navegar
    cy.contains('td', nombreMadre, { timeout: 15000 })
      .parents('tr')
      .find('a.btn-success')
      .invoke('attr', 'href') // Extraemos la URL: /sistema/madre/.../registrar/
      .then((href) => {
        cy.log('Navegando a: ' + href);
        cy.visit(href); // ¡Navegación directa e infalible!
      });


    // --- FASE 3: LLENAR PARTO ---
    cy.log('📌 FASE 3: Datos Clínicos');
    // Verificamos que llegamos al formulario correcto
    cy.contains('h2', 'Registro de Parto', { timeout: 10000 }).should('be.visible');

    cy.get('select[name="tipo_parto"]').select('Cesárea Urgencia');
    cy.get('select[name="anestesia"]').select('Raquídea');
    cy.get('input[name="fecha_parto_date"]').type('2025-11-23');
    cy.get('input[name="fecha_parto_time"]').type('14:30');
    cy.get('input[name="edad_gestacional"]').type('39');
    cy.get('input[name="corticoides"][value="No"]').check();


    // --- FASE 4: LLENAR RN ---
    cy.log('📌 FASE 4: Datos RN');
    cy.get('select[name="sexo"]').select('Femenino');
    cy.get('input[name="estado_al_nacer"][value="Vivo"]').check();
    cy.get('input[name="peso_gramos"]').type('3450');
    cy.get('input[name="talla_cm"]').type('50.5');
    cy.get('input[name="apgar_1_min"]').type('9');
    cy.get('input[name="apgar_5_min"]').type('10');
    cy.get('input[name="profilaxis_vit_k"]').check();
    cy.get('input[name="profilaxis_oftalmica"]').check();


    // --- FASE 5: GUARDAR ---
    cy.get('button[type="submit"]').click();

    // Validación Final
    cy.contains('h2', 'Detalle del Parto', { timeout: 20000 }).should('be.visible');
    cy.contains('Información del Parto').should('be.visible');
    cy.contains('3450').should('be.visible');
  });
});