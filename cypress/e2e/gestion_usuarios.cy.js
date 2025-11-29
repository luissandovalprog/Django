describe('Administración: Gestión de Usuarios y Roles', () => {

  // Generamos datos aleatorios para no repetir usuarios
  const timestamp = Date.now().toString().slice(-4);
  const nuevoUsuario = `usuario_test_${timestamp}`;
  const rutUsuario = `15.111.${timestamp}-k`; 

  beforeEach(() => {
    cy.viewport(1280, 720);
    
    // 1. Login como Admin de Sistema
    cy.visit('/accounts/login/');
    cy.get('input[name="username"]').type('adminsistema'); 
    cy.get('input[name="password"]').type('Hospital2025');
    cy.get('button[type="submit"]').click();
    
    // Validación de sesión (no estar en login)
    cy.url({ timeout: 20000 }).should('not.include', '/accounts/login/');
    cy.get('.navbar', { timeout: 10000 }).should('be.visible');
  });

  it('Debe crear un nuevo usuario "Matrona" y verificar que aparece en la lista', () => {
    // 2. Navegar a Gestión de Usuarios
    cy.visit('/accounts/gestion/');
    cy.contains('h2', 'Gestión de Usuarios').should('be.visible');

    // 3. Clic en "Nuevo Usuario"
    // Usamos cy.contains con un selector más amplio por si el texto varía ligeramente
    cy.contains('a', 'Nuevo Usuario').click();
    cy.contains('h2', 'Nuevo Usuario').should('be.visible');

    // 4. Llenar Formulario
    cy.log('👤 Creando nuevo usuario...');
    
    cy.get('input[name="username"]').type(nuevoUsuario);
    cy.get('input[name="email"]').type(`${nuevoUsuario}@hospital.cl`);
    cy.get('input[name="nombre_completo"]').type('Matrona de Prueba Cypress');
    cy.get('input[name="rut"]').type(rutUsuario);
    
    // --- CORRECCIÓN AQUÍ ---
    // Seleccionamos "Matrona" en lugar de "Matrona Clínica"
    // Cypress buscará la opción que tenga el texto "Matrona"
    cy.get('select[name="rol"]').select('Matrona');
    
    cy.get('input[name="password1"]').type('ClaveSegura123');
    cy.get('input[name="password2"]').type('ClaveSegura123');
    cy.get('input[name="activo"]').check();

    // 5. Guardar
    cy.get('button[type="submit"]').click();

    // 6. Validar Éxito
    cy.url().should('include', '/accounts/gestion/');
    
    // Verificamos que el usuario aparezca en la tabla
    cy.contains('td', nuevoUsuario).should('be.visible');
    // Verificamos que su rol se guardó bien
    cy.contains('td', 'Matrona').should('be.visible');
  });

  it('Debe desactivar un usuario existente', () => {
    // 1. Ir a gestión
    cy.visit('/accounts/gestion/');
    
    // 2. Buscar al usuario (nuevoUsuario)
    // Nota: Si corres este test aislado sin correr el anterior, fallará porque el usuario no existe.
    // Para pruebas reales, idealmente deberías crear el usuario dentro de este test también (before),
    // pero para este ejercicio asumiremos que corren en secuencia.
    
    // Buscamos la fila del usuario
    cy.contains('tr', nuevoUsuario).within(() => {
      // Buscar el botón de desactivar por su título o clase
      // Si no tiene title, buscamos el botón rojo (clase danger o color)
      cy.get('button').first().click();
    });

    // Validar cambio visual (Badge Inactivo o color rojo)
    // Esperamos que el texto cambie a "Inactivo" o que el icono cambie
    cy.contains('tr', nuevoUsuario).should('contain', 'Inactivo');
  });
});