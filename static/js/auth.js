/* 버튼 */
const GoButton = document.getElementById('goBtn');
const SignUpButton = document.getElementById('signUpBtn');

/* 토큰  */
const token = localStorage.getItem('userToken');
console.log('현재 읽어온 토큰 값:', token);

/* 람다식 */
const pwRegex = /^[a-zA-Z0-9]{4,16}$/;

if (token) 
{
    fetch('/api/verify',
    {
        method: 'POST',
        headers: 
        { 
            'Content-Type': 'application/json' 
        },
        body: JSON.stringify({ token: token })
    })
    .then(response => response.json())
    .then(data => 
        {
            if (data.result === 'success') 
        {
            window.location.href = '/room';
        } else 
        {
            localStorage.removeItem('userToken');
        }
    });
}

GoButton.addEventListener('click', () => 
{
    const UID_V = document.getElementById('userId').value.trim();
    const UP_V = document.getElementById('userPassword').value;

    if (!UID_V || !UP_V) 
    {
        alert('아이디와 비밀번호를 모두 입력해주세요.');
        return;
    }

    if (!pwRegex.test(UP_V)) 
    {
        alert('비밀번호는 4~16자의 영문 대소문자와 숫자만 사용 가능합니다.');
        return; 
    }
    
    const loginData = 
    {
        userId: UID_V,
        userPw: UP_V
    };

    fetch('/api/login', 
    {
        method: 'POST',
        headers: 
        {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(loginData)
    })
    .then(response => response.json())
    .then(data => 
    {
        if (data.result === 'success') 
        {
            localStorage.setItem('userToken', data.token);
            
            alert('로그인 성공!');
            window.location.href = '/room';
        } else 
        {
            alert('로그인 실패: ' + data.message);
        }
    })
    .catch(error => 
    {
        console.error('통신 에러:', error);
    });

});

SignUpButton.addEventListener('click', () => 
{
    const NUID_V = document.getElementById('newUserId').value.trim();
    const NUP_V = document.getElementById('newUserPassword').value;
    const CUP_V = document.getElementById('confirmPassword').value;

    if (!NUID_V || !NUP_V || !CUP_V) 
    {
        alert('아이디와 비밀번호를 모두 입력해주세요.');
        return;
    }

    if (!pwRegex.test(NUP_V)) 
    {
        alert('비밀번호는 4~16자의 영문 대소문자와 숫자만 사용 가능합니다.');
        return; 
    }

    if (NUP_V !== CUP_V) 
    {
        alert('비밀번호가 일치하지 않습니다.');
        return;
    }

    const userData = 
    {
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
    .then(response => response.json()).then(data => 
    {
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
        console.error("통신 에러:", error);
    });
});