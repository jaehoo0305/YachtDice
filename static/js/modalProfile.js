const profileBtn = document.querySelector('.profile-btn');
const profileModal = document.getElementById('profileModal');
const closeProfileBtn = document.getElementById('closeProfileBtn');

const userIdChange = document.getElementById('userIdChange');

let t = 0;

profileBtn.addEventListener('click', () =>
{
  profileModal.classList.remove('hidden');
});

closeProfileBtn.addEventListener('click', () => 
{
  profileModal.classList.add('hidden');
});

userIdChange.addEventListener('keydown', function(event) 
{
  alert('이름 변경을 실패했습니다.');
});