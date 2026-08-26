/* 사용자 입력 값은 함수 안에 있어야 한다 */
const UID_V = document.getElementById('userId').value;
const UP_V = document.getElementById('userPassword').value;

/* 버튼 */
const GoButton = document.getElementById('goBtn');
const SignUpButton = document.getElementById('signUpBtn');

SignUpButton.addEventListener('click', () => 
{
    const NUID_V = document.getElementById('newUserId').value;
    const NUP_V = document.getElementById('newUserPassword').value;
    const CUP_V = document.getElementById('confirmPassword').value;

    if (NUP_V !== CUP_V) 
    {
        alert('비밀번호가 일치하지 않습니다.');
        return;
    }

    const userData = {
        userId: NUID_V,
        userPw: NUP_V
    };

    fetch('/api/register', 
    {
        method: 'POST', 
        headers: 
        {
            'Content-Type': 'application/json' 
        },
        body: JSON.stringify(userData) 
    })

    .then(response => response.json()).then(data => {
        if (data.result === 'success') 
        {
          alert("회원가입이 완료되었습니다!");
        } else 
        {
          alert("가입 실패: " + data.message);
        }
    })
    .catch(error =>
    {
        console.error("통신 에러 발생:", error);
    });
});