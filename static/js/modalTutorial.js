const tutorialBtn = document.querySelector('.tutorial-btn');
const tutorialModal = document.getElementById('tutorialModal');
const closeTutorialBtn = document.getElementById('closeTutorialBtn');

tutorialBtn.addEventListener('click', () => 
{
  tutorialModal.classList.remove('hidden');
});

closeTutorialBtn.addEventListener('click', () => 
{
  tutorialModal.classList.add('hidden');
});