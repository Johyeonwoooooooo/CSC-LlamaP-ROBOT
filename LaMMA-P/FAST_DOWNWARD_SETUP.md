# Fast Downward 설치 (downward/ 가 repo에서 제외된 이유)

LaMMA-P는 PDDL 플래너로 [Fast Downward](https://github.com/aibasel/downward)를 사용한다.
용량(빌드 바이너리 ~145MB) 때문에 `LaMMA-P/downward/` 는 git에서 **제외**(.gitignore)했다.
원본 LaMMA-P에서도 이건 git **submodule**(aibasel/downward)이다.

클론한 뒤 아래로 받아서 빌드하면 된다 (커밋 `e02b0f84296337d191610cf93646c1a70d2b11d3` 고정):

```bash
cd LaMMA-P
curl -sSL -o /tmp/fd.tar.gz \
  https://github.com/aibasel/downward/archive/e02b0f84296337d191610cf93646c1a70d2b11d3.tar.gz
tar xzf /tmp/fd.tar.gz
mv downward-e02b0f84296337d191610cf93646c1a70d2b11d3 downward
cd downward && python3 build.py        # cmake + g++ 필요, 수 분 소요
./fast-downward.py --help              # 확인
```

빌드 결과 `downward/builds/release/bin/downward` 가 생기면 OK.
