function updateStatus(id, newStatus) {
    fetch(`/api/update_status/${id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
    })
    .then(response => response.json())
    .then(data => {
        if(data.success) {
            // Визуальное уведомление или изменение цвета
            location.reload(); // Для простоты обновляем страницу для пересчета KPI
        } else {
            alert('Ошибка обновления');
        }
    });
}