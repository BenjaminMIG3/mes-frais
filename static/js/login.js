document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const container = document.querySelector('.card');
    
    function showAlert(message, type) {
        // Supprime les anciennes alertes
        const oldAlert = container.querySelector('.alert');
        if (oldAlert) oldAlert.remove();
        // Crée la nouvelle alerte
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.role = 'alert';
        alert.textContent = message;
        container.prepend(alert);
    }

    form.addEventListener('submit', async function(event) {
        event.preventDefault();
        const formData = new FormData(this);
        const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;
        const response = await fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        const data = await response.json();
        if (response.status === 200) {
            showAlert(data.message, 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        } else {
            showAlert(data.message, 'danger');
        }
    });
});