function search(){
    let search_query = ""
    if(document.getElementById("search-input-desktop").value.length > 0){
        search_query = document.getElementById("search-input-desktop").value
    }else{
        search_query = document.getElementById("search-input-mobile").value
    }

    document.location = `/feed?q=${search_query}`
}

document.getElementById("search-input-desktop").addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        search()
    }}
)

document.getElementById("search-input-mobile").addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        search()
    }}
)

function fillSearchWithAutocomplete(search_suggestion){
    document.getElementById("autocomplete-wrapper-desktop").style.display = "none";
    document.getElementById("autocomplete-wrapper-mobile").style.display = "none";
    document.getElementById('search-input-desktop').value = search_suggestion;
    document.getElementById('search-input-mobile').value = search_suggestion;
    search()
}


let debounceTimer;
const debounce = (func, delay) => {
    return (...args) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => func.apply(this, args), delay);
    };
};

const fetchAndDisplaySuggestions = async (query, type) => {
    const autocompleteWrapper = document.getElementById(`autocomplete-wrapper-${type}`);

    if (query.length < 1) {
        autocompleteWrapper.innerHTML = '';
        autocompleteWrapper.style.display = 'none';
        return;
    }

    try {
        const response = await fetch(`/autocomplete?q=${encodeURIComponent(query)}`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const suggestions = await response.json();

        autocompleteWrapper.innerHTML = '';

        if (suggestions && suggestions.length > 0) {
            suggestions.forEach(suggestionText => {
                const p = document.createElement('p');
                p.className = 'autocomplete-suggestion';

                p.setAttribute('onclick', `fillSearchWithAutocomplete('${suggestionText.replace(/'/g, "\\'")}')`);

                p.innerHTML = `<i class="bi bi-search"></i> <span class="search-suggestion-text">${suggestionText}</span>`;

                autocompleteWrapper.appendChild(p);
            });
            autocompleteWrapper.style.display = 'block';
        } else {
            autocompleteWrapper.style.display = 'none';
        }
    } catch (error) {
        console.error('Error fetching autocomplete suggestions:', error);
        autocompleteWrapper.style.display = 'none';
    }
};

const debouncedFetch = debounce(fetchAndDisplaySuggestions, 300);

document.getElementById('search-input-desktop').addEventListener('input', (e) => {
    debouncedFetch(e.target.value, 'desktop');
});

document.getElementById('search-input-mobile').addEventListener('input', (e) => {
    debouncedFetch(e.target.value, 'mobile');
});

document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-wrapper')) {
        document.getElementById('autocomplete-wrapper-desktop').style.display = 'none';
        document.getElementById('autocomplete-wrapper-mobile').style.display = 'none';
    }
});

window.addEventListener("DOMContentLoaded", function e(){
    {
        let current_id_from_url = document.location.hash.replace("#tab_", "")
        if(current_id_from_url){
            tabSwitcher(document.getElementById(`switcher_${current_id_from_url}`), current_id_from_url)
        }
    }
})
function tabSwitcher(trigger_elem, selected_tab){
    if(document.getElementsByClassName('profile-tab-selection selected-selector').length > 0){
        document.getElementsByClassName('selected-tab')[0].className = "tab";
        document.getElementsByClassName("profile-tab-selection selected-selector")[0].className = "profile-tab-selection"
    }
    document.getElementById("mobile-menu").style.display = "none"

    trigger_elem.className = "profile-tab-selection selected-selector";
    document.getElementById(selected_tab).className = "selected-tab";
    document.location = `#tab_${selected_tab}`
}

window.addEventListener("DOMContentLoaded", function() {
    const reviewModalOverlay = document.getElementById('review-modal-overlay');
    const closeButton = document.querySelector('.close-modal');
    const cancelButton = document.querySelector('.modal-button.cancel-button');
    const submitButton = document.querySelector('.modal-button.submit-button');
    const rateButtons = document.querySelectorAll('.order-colorful-button.yellow-theme');
    const modalProductImage = document.querySelector('.modal-product-image');
    const modalProductName = document.querySelector('.modal-product-name');
    const stars = document.querySelectorAll('.stars-container i');
    const selectedRatingInput = document.getElementById('selected-rating');
    const reviewCommentTextarea = document.getElementById('review-comment');

    let currentRating = 0;
    let currentOrderId = null;

    function openReviewModal(productImage, productName, orderId) {
        modalProductImage.style.backgroundImage = `url('${productImage}')`;
        modalProductName.textContent = productName;
        currentOrderId = orderId;
        reviewModalOverlay.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        resetRatingAndComment();
    }

    function closeReviewModal() {
        reviewModalOverlay.style.display = 'none';
        document.body.style.overflow = '';
        resetRatingAndComment();
        currentOrderId = null;
    }

    function resetRatingAndComment() {
        currentRating = 0;
        stars.forEach(star => {
            star.classList.remove('bi-star-fill');
            star.classList.add('bi-star');
        });
        selectedRatingInput.value = 0;
        reviewCommentTextarea.value = '';
    }

    function updateStars() {
        stars.forEach(star => {
            const starValue = parseInt(star.dataset.value);
            if (starValue <= currentRating) {
                star.classList.remove('bi-star');
                star.classList.add('bi-star-fill');
            } else {
                star.classList.remove('bi-star-fill');
                star.classList.add('bi-star');
            }
        });
    }

    rateButtons.forEach(button => {
        button.addEventListener('click', function() {
            const orderDiv = this.closest('.order');
            const orderDetailsDiv = orderDiv.querySelector('.order-details'); // Get the specific div with the ID
            if (orderDiv && orderDetailsDiv && orderDetailsDiv.id) {
                const orderId = orderDetailsDiv.id; // Extract the ID
                const productImage = orderDiv.querySelector('.order-image').style.backgroundImage.replace('url("', '').replace('")', '');
                const productName = orderDiv.querySelector('.order-details-product-name').textContent;
                openReviewModal(productImage, productName, orderId); // Pass the extracted ID
            } else {
                console.error('Order details div or its ID not found for this product.');
                alert('Ürün değerlendirilemiyor: Sipariş bilgisi eksik.');
            }
        });
    });

    closeButton.addEventListener('click', closeReviewModal);
    cancelButton.addEventListener('click', closeReviewModal);
    reviewModalOverlay.addEventListener('click', function(event) {
        if (event.target === reviewModalOverlay) {
            closeReviewModal();
        }
    });

    stars.forEach(star => {
        star.addEventListener('click', function() {
            currentRating = parseInt(this.dataset.value);
            selectedRatingInput.value = currentRating;
            updateStars();
        });

        star.addEventListener('mouseover', function() {
            const hoverValue = parseInt(this.dataset.value);
            stars.forEach((s, index) => {
                if (index < hoverValue) {
                    s.classList.remove('bi-star');
                    s.classList.add('bi-star-fill');
                } else {
                    s.classList.remove('bi-star-fill');
                    s.classList.add('bi-star');
                }
            });
        });

        star.addEventListener('mouseout', function() {
            updateStars();
        });
    });
    submitButton.addEventListener('click', async function() {
        const rating = selectedRatingInput.value;
        const comment = reviewCommentTextarea.value;

        if (rating === "0") {
            alert('Lütfen bir yıldız derecelendirmesi seçin!');
            return;
        }

        if (!currentOrderId) {
            console.error('No order ID found for review submission. Modal was opened without an orderId.');
            alert('Değerlendirme gönderilemiyor: Ürün bilgisi eksik.');
            return;
        }

        try {
            const response = await fetch(`/review?order=${currentOrderId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    order_id: currentOrderId,
                    rating: parseInt(rating),
                    comment: comment
                })
            });

            if (response.ok) {
                alert('Değerlendirmeniz başarıyla gönderildi!');
                closeReviewModal();
            } else {
                const errorData = await response.text();
                console.error('Değerlendirme gönderilirken hata oluştu:', response.status, errorData);
                alert(`Değerlendirme gönderilemedi: ${response.status} - ${errorData || 'Sunucu hatası'}`);
            }
        } catch (error) {
            console.error('Ağ hatası:', error);
            alert('Değerlendirme gönderilirken bir ağ hatası oluştu. Lütfen internet bağlantınızı kontrol edin.');
        }
    });
});

