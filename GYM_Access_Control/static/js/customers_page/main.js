document.addEventListener('DOMContentLoaded', function () {
  const buttons = document.querySelectorAll('.open-modal');

  const register_button = document.querySelectorAll('.register-modal')

  
  buttons.forEach(button => {
    button.addEventListener('click', () => {
        $('#customerModal').modal('show');  
      const fullName = button.getAttribute('data-fullname');
      const phone = button.getAttribute('data-phone');
      const type = button.getAttribute('data-type');
      const status = button.getAttribute('data-status');
      const images = JSON.parse(button.getAttribute('data-images') || '[]');

      document.getElementById('modalFullName').textContent = fullName;
      document.getElementById('modalPhoneNumber').textContent = phone;
      document.getElementById('modalCustomerType').textContent = type;
      document.getElementById('modalStatus').textContent = status;
      const imageContainer = document.getElementById('modalImages');
      imageContainer.innerHTML = ''; 

      images.forEach(url => {
        const img = document.createElement('img');
        img.src = url;
        img.className = 'img-thumbnail';
        img.style.width = '100px';
        img.style.height = '100px';
        img.style.objectFit = 'cover';
        imageContainer.appendChild(img);
      });
    });
  });
  
  register_button.forEach(button => {
    button.addEventListener('click',() => {
        $('#addCustomerModal').modal('show');})


  });

  delete_button.forEach(button=> {
    button.addEventListener('click', ()=>{
      $('#deleteCustomerModal').mo
    })
  })

  
});
function getCSRFToken() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) {
            return decodeURIComponent(cookie.substring(name.length + 1));
        }
    }
    return null;
}

function deleteCustomer(customerId) {
    if (!confirm("Bu müşteriyi silmek istediğinizden emin misiniz?")) return;

    fetch('/delete-customer/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ id: customerId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const row = document.getElementById(`customer-${customerId}`);
            if (row) row.remove();
        } else {
            alert("Silme işlemi başarısız: " + (data.error || 'Bilinmeyen hata'));
        }
    });
}
