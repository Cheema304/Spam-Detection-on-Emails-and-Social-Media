(() => {
  const box = document.getElementById('message');
  const count = document.getElementById('char-count');
  if (box && count) {
    const update = () => count.textContent = `${box.value.length.toLocaleString()} / 8,000 characters`;
    box.addEventListener('input', update);
    update();
  }
})();
