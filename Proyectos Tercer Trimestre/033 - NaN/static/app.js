document.addEventListener("click", e => {
    const card = e.target.closest(".subject-card");

    if(card){
        card.style.opacity = "0.8";
    }
});
