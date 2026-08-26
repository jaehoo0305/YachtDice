const enterBtn = document.querySelector('.enter-btn');
const EnterModal = document.getElementById('enterModal');
const closeEnterBtn = document.getElementById('closeEnterBtn');
const roomInput = document.getElementById('roomNum');

enterBtn.addEventListener('click', () =>
{
  enterModal.classList.remove('hidden');
});

closeEnterBtn.addEventListener('click', () => 
{
  enterModal.classList.add('hidden');
});


roomInput.addEventListener('keydown', function(event) {
  if (event.key === 'Enter') {
    checkRoom();
  }
});

async function checkRoom() {
  const roomValue = roomInput.value;
  console.log('입력된 방 번호:', roomValue);

  if (!roomValue || roomValue.trim() === "") {
    alert("방 번호를 입력해주세요.");
    return;
  }

  try {
    const response = await fetch('/api/create-room', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ room_id: roomValue.trim() })
    });

    const data = await response.json();

    if (response.ok && data.result === 'success') {
      window.location.href = data.redirect_url;
    } else {
      alert(data.message || "방 입장에 실패했습니다.");
    }
  } catch (error) {
    console.error("통신 오류:", error);
    alert("서버와 통신 중 오류가 발생했습니다.");
  }
}