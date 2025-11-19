/**
 * Sistema de Notificaciones - SIGN
 * Patrón: Carga Basada en Eventos (Navegación + Interacción)
 */

class NotificationSystem {
  constructor() {
    this.bellButton = document.getElementById("notifications-bell");
    this.badge = document.getElementById("notifications-badge");
    this.dropdown = document.getElementById("notifications-dropdown");
    this.overlay = document.getElementById("notifications-overlay");
    this.listContainer = document.getElementById("notifications-list");
    this.markAllBtn = document.getElementById("btn-mark-all-read");

    this.isOpen = false;
    this.notificationsLoaded = false;
    this.currentCount = 0;

    // Configuración
    this.config = {
      pollingInterval: 60000, // 60 segundos
      maxNotifications: 10,
      apiUrls: {
        count: "/notifications/api/conteo/",
        list: "/notifications/api/lista/",
        markRead: "/notifications/api/marcar-leida/",
        markAllRead: "/notifications/api/marcar-todas-leidas/",
        delete: "/notifications/api/eliminar/",
      },
    };

    this.init();
  }

  /**
   * Inicializar el sistema
   */
  init() {
    if (!this.bellButton) return;

    // Evento de Navegación: Cargar conteo al cargar la página
    this.loadNotificationCount();

    // Evento de Interacción: Cargar lista al hacer click
    this.bellButton.addEventListener("click", (e) => {
      e.stopPropagation();
      this.toggleDropdown();
    });

    // Cerrar dropdown al hacer click fuera
    this.overlay?.addEventListener("click", () => {
      this.closeDropdown();
    });

    // Marcar todas como leídas
    this.markAllBtn?.addEventListener("click", () => {
      this.markAllAsRead();
    });

    // Polling periódico para actualizar el conteo
    this.startPolling();

    console.log("✅ Sistema de notificaciones inicializado");
  }

  /**
   * Cargar el conteo de notificaciones no leídas
   * Se ejecuta al cargar cualquier página (Evento de Navegación)
   */
  async loadNotificationCount() {
    try {
      const response = await fetch(this.config.apiUrls.count, {
        method: "GET",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      });

      if (!response.ok) throw new Error("Error al cargar notificaciones");

      const data = await response.json();

      if (data.success) {
        this.updateBadge(data.count);
      }
    } catch (error) {
      console.error("Error al cargar conteo de notificaciones:", error);
    }
  }

  /**
   * Cargar la lista completa de notificaciones
   * Se ejecuta SOLO cuando el usuario hace click en la campana (Evento de Interacción)
   */
  async loadNotificationList() {
    if (!this.listContainer) return;

    // Mostrar loading
    this.listContainer.innerHTML = this.getLoadingHTML();

    try {
      const response = await fetch(
        `${this.config.apiUrls.list}?limit=${this.config.maxNotifications}`,
        {
          method: "GET",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
          },
        }
      );

      if (!response.ok) throw new Error("Error al cargar lista");

      const data = await response.json();

      if (data.success) {
        this.renderNotifications(data.notificaciones);
        this.notificationsLoaded = true;

        // Actualizar badge con el conteo real
        this.updateBadge(data.count_no_leidas);
      }
    } catch (error) {
      console.error("Error al cargar lista de notificaciones:", error);
      this.listContainer.innerHTML = this.getErrorHTML();
    }
  }

  /**
   * Renderizar las notificaciones en el dropdown
   */
  renderNotifications(notifications) {
    if (!this.listContainer) return;

    if (notifications.length === 0) {
      this.listContainer.innerHTML = this.getEmptyHTML();
      return;
    }

    const html = notifications
      .map((notif) => this.getNotificationHTML(notif))
      .join("");
    this.listContainer.innerHTML = html;

    // Agregar listeners a cada notificación
    this.listContainer
      .querySelectorAll(".notification-item")
      .forEach((item) => {
        item.addEventListener("click", (e) => {
          const notifId = item.dataset.id;

          // Redirigir a la vista de detalle de la notificación
          // La vista se encargará de marcarla como leída y mostrar los detalles
          window.location.href = `/notifications/${notifId}/`;
        });
      });

    // Agregar listeners a los botones de eliminar
    this.listContainer
      .querySelectorAll(".notification-delete-btn")
      .forEach((btn) => {
        btn.addEventListener("click", (e) => {
          e.stopPropagation(); // Evitar que se active el click de la notificación
          const notifId = btn.dataset.notifId;
          this.deleteNotification(notifId);
        });
      });
  }

  /**
   * HTML de una notificación individual
   */
  getNotificationHTML(notif) {
    const unreadClass = !notif.leida ? "unread" : "";
    const icon = this.getNotificationIcon(notif.tipo);

    // Botón de eliminar solo para notificaciones leídas
    const deleteButton = notif.leida
      ? `
            <button class="notification-delete-btn" data-notif-id="${notif.id}" title="Eliminar notificación">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    <line x1="10" y1="11" x2="10" y2="17"></line>
                    <line x1="14" y1="11" x2="14" y2="17"></line>
                </svg>
            </button>
        `
      : "";

    return `
            <div class="notification-item ${unreadClass}" 
                 data-id="${notif.id}" 
                 data-link="${notif.link}"
                 data-read="${notif.leida}">
                <div class="notification-content">
                    <div class="notification-title">
                        <span class="notification-type-badge ${notif.tipo}">
                            ${notif.tipo}
                        </span>
                        <span>${notif.titulo}</span>
                    </div>
                    <div class="notification-message">
                        ${notif.mensaje}
                    </div>
                    <div class="notification-time">
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <polyline points="12 6 12 12 16 14"/>
                        </svg>
                        ${notif.fecha}
                    </div>
                </div>
                ${deleteButton}
            </div>
        `;
  }

  /**
   * HTML de estado vacío
   */
  getEmptyHTML() {
    return `
            <div class="notifications-empty">
                <div class="notifications-empty-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                        <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
                    </svg>
                </div>
                <p>No tienes notificaciones</p>
            </div>
        `;
  }

  /**
   * HTML de loading
   */
  getLoadingHTML() {
    return `
            <div class="notifications-loading">
                <div class="spinner-notifications"></div>
                <p style="color: var(--gray-500); font-size: 14px; margin: 0;">Cargando notificaciones...</p>
            </div>
        `;
  }

  /**
   * HTML de error
   */
  getErrorHTML() {
    return `
            <div class="notifications-empty">
                <div class="notifications-empty-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                    </svg>
                </div>
                <p>Error al cargar notificaciones</p>
            </div>
        `;
  }

  /**
   * Obtener icono según tipo
   */
  getNotificationIcon(type) {
    const icons = {
      correccion: "📝",
      parto: "👶",
      sistema: "🔔",
    };
    return icons[type] || "🔔";
  }

  /**
   * Actualizar el badge con el conteo
   */
  updateBadge(count) {
    this.currentCount = count;

    if (count > 0) {
      this.badge.textContent = count > 99 ? "99+" : count;
      this.badge.classList.remove("hidden");
      this.bellButton.classList.add("has-notifications");
    } else {
      this.badge.classList.add("hidden");
      this.bellButton.classList.remove("has-notifications");
    }
  }

  /**
   * Abrir/cerrar dropdown
   */
  toggleDropdown() {
    if (this.isOpen) {
      this.closeDropdown();
    } else {
      this.openDropdown();
    }
  }

  /**
   * Abrir dropdown
   */
  openDropdown() {
    this.isOpen = true;
    this.dropdown.classList.add("show");
    this.overlay?.classList.add("show");

    // Cargar lista solo si no se ha cargado antes
    if (!this.notificationsLoaded) {
      this.loadNotificationList();
    }
  }

  /**
   * Cerrar dropdown
   */
  closeDropdown() {
    this.isOpen = false;
    this.dropdown.classList.remove("show");
    this.overlay?.classList.remove("show");
  }

  /**
   * Marcar una notificación como leída
   */
  async markAsRead(notificationId) {
    try {
      const response = await fetch(this.config.apiUrls.markRead, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": this.getCSRFToken(),
        },
        body: JSON.stringify({
          notificacion_id: notificationId,
        }),
      });

      if (!response.ok) throw new Error("Error al marcar como leída");

      const data = await response.json();

      if (data.success) {
        // Actualizar UI
        const item = document.querySelector(`[data-id="${notificationId}"]`);
        if (item) {
          item.classList.remove("unread");
          item.dataset.read = "true";
        }

        // Actualizar badge
        this.updateBadge(data.nuevo_conteo);

        // Recargar para mostrar el botón de eliminar
        this.notificationsLoaded = false;
        this.loadNotificationList();
      }
    } catch (error) {
      console.error("Error al marcar notificación como leída:", error);
    }
  }

  /**
   * Eliminar una notificación (solo si está leída)
   */
  async deleteNotification(notificationId) {
    try {
      const response = await fetch(this.config.apiUrls.delete, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": this.getCSRFToken(),
        },
        body: JSON.stringify({
          notificacion_id: notificationId,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        console.error("Error al eliminar:", data.error);
        alert(data.error || "Error al eliminar la notificación");
        return;
      }

      const data = await response.json();

      if (data.success) {
        // Remover la notificación del DOM con animación
        const item = document.querySelector(`[data-id="${notificationId}"]`);
        if (item) {
          item.style.opacity = "0";
          item.style.transform = "translateX(20px)";
          item.style.transition = "all 0.3s ease";

          setTimeout(() => {
            item.remove();

            // Verificar si quedan notificaciones
            const remaining =
              this.listContainer.querySelectorAll(".notification-item");
            if (remaining.length === 0) {
              this.listContainer.innerHTML = this.getEmptyHTML();
            }
          }, 300);
        }

        // Recargar la lista para actualizar conteos
        this.notificationsLoaded = false;
        if (this.isOpen) {
          setTimeout(() => this.loadNotificationList(), 350);
        }

        console.log("✅ Notificación eliminada correctamente");
      }
    } catch (error) {
      console.error("Error al eliminar notificación:", error);
      alert("Error al eliminar la notificación");
    }
  }

  /**
   * Marcar todas como leídas
   */
  async markAllAsRead() {
    try {
      const response = await fetch(this.config.apiUrls.markAllRead, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": this.getCSRFToken(),
        },
      });

      if (!response.ok) throw new Error("Error al marcar todas como leídas");

      const data = await response.json();

      if (data.success) {
        // Recargar lista para mostrar los botones de eliminar
        this.notificationsLoaded = false;
        this.loadNotificationList();

        // Actualizar badge
        this.updateBadge(0);

        console.log(`✅ ${data.count} notificaciones marcadas como leídas`);
      }
    } catch (error) {
      console.error("Error al marcar todas como leídas:", error);
    }
  }

  /**
   * Iniciar polling periódico
   */
  startPolling() {
    setInterval(() => {
      // Solo actualizar conteo si el dropdown está cerrado
      if (!this.isOpen) {
        this.loadNotificationCount();
      }
    }, this.config.pollingInterval);
  }

  /**
   * Obtener CSRF Token
   */
  getCSRFToken() {
    // 1. Intentar leer del meta tag (Solución Segura)
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) {
      return meta.content;
    }

    // 2. Fallback: Intentar leer de un input de formulario si existe
    const input = document.querySelector("[name=csrfmiddlewaretoken]");
    if (input) {
      return input.value;
    }

    // 3. Fallback antiguo: Cookies (Solo funciona si HTTPOnly=False)
    const name = "csrftoken";
    // ... (puedes dejar tu código antiguo aquí como último recurso)
    return null;
  }
}

// Inicializar cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", () => {
  window.notificationSystem = new NotificationSystem();
});
