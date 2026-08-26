const enterBtn = document.querySelector('.enter-btn');
const EnterModal = document.getElementById('enterModal');
const closeEnterBtn = document.getElementById('closeEnterBtn');

enterBtn.addEventListener('click', () =>
{
  enterModal.classList.remove('hidden');
});

closeEnterBtn.addEventListener('click', () => 
{
  enterModal.classList.add('hidden');
});