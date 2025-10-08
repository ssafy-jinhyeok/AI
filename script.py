import requests
import hashlib
import os
import re
import time

class GitHubImageUploader:
    def __init__(self, token, repo_owner, repo_name, branch='main'):
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.branch = branch
        self.api_base = 'https://api.github.com'
    
    def upload_base64_image(self, base64_string, file_path):
        """BASE64 이미지를 GitHub에 업로드"""
        url = f'{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}'
        
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        data = {
            'message': f'Upload image: {file_path}',
            'content': base64_string,
            'branch': self.branch
        }
        
        response = requests.put(url, json=data, headers=headers)
        
        if response.status_code == 201:
            result = response.json()
            return result['content']['download_url']
        else:
            raise Exception(f"Upload failed: {response.status_code} - {response.text}")


class NotebookImageProcessor:
    def __init__(self, uploader, image_folder='notebook_images'):
        self.uploader = uploader
        self.image_folder = image_folder
        self.stats = {
            'notebooks': 0,
            'images': 0,
            'errors': 0
        }
    
    def generate_hash_filename(self, base64_string):
        """BASE64 문자열의 해시값으로 파일명 생성"""
        hash_hex = hashlib.sha256(base64_string.encode()).hexdigest()[:16]
        return f"{hash_hex}.png"
    
    def find_notebooks(self, base_folder='.'):
        """모든 .ipynb 파일 찾기"""
        notebooks = []
        for root, dirs, files in os.walk(base_folder):
            # .ipynb_checkpoints 폴더 제외
            dirs[:] = [d for d in dirs if d != '.ipynb_checkpoints']
            for file in files:
                if file.endswith('.ipynb'):
                    notebooks.append(os.path.join(root, file))
        return notebooks
    
    def process_notebook(self, notebook_path):
        """노트북 파일의 BASE64 이미지를 찾아서 업로드 후 치환"""
        print(f"\n처리 중: {notebook_path}")
        
        try:
            # 파일을 텍스트로 읽기
            with open(notebook_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # BASE64 패턴 찾기 (최소 100자 이상의 BASE64 문자열)
            # 이미지 데이터는 보통 매우 길기 때문에 짧은 문자열은 제외
            pattern = r'"([A-Za-z0-9+/]{100,}={0,2})"'
            matches = re.findall(pattern, content)
            
            if not matches:
                print("  - BASE64 이미지 없음")
                return
            
            print(f"  발견된 BASE64 문자열: {len(matches)}개")
            
            # 중복 제거 (동일한 이미지가 여러 번 나올 수 있음)
            unique_matches = list(set(matches))
            print(f"  고유 이미지: {len(unique_matches)}개")
            
            replaced_count = 0
            
            for idx, base64_str in enumerate(unique_matches, 1):
                # BASE64 문자열이 실제로 이미지인지 간단히 확인
                # (너무 짧거나 패턴이 이상한 경우 스킵)
                if len(base64_str) < 200:
                    continue
                
                try:
                    # 파일명 생성
                    filename = self.generate_hash_filename(base64_str)
                    github_path = f"{self.image_folder}/{filename}"
                    
                    print(f"  [{idx}/{len(unique_matches)}] 업로드 중: {filename}...", end=' ')
                    
                    # GitHub에 업로드
                    url = self.uploader.upload_base64_image(base64_str, github_path)
                    
                    # 원본 문자열을 URL로 치환
                    content = content.replace(f'"{base64_str}"', f'"{url}"')
                    
                    replaced_count += 1
                    self.stats['images'] += 1
                    
                    print(f"✓")
                    
                    # Rate limit 방지
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"✗ ({str(e)})")
                    self.stats['errors'] += 1
            
            # 변경사항이 있으면 파일 저장
            if replaced_count > 0:
                with open(notebook_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✓ 완료: {replaced_count}개 이미지 업로드 및 치환")
                self.stats['notebooks'] += 1
            
        except Exception as e:
            print(f"  ✗ 에러: {str(e)}")
            self.stats['errors'] += 1
    
    def process_all(self, base_folder='.'):
        """모든 노트북 처리"""
        notebooks = self.find_notebooks(base_folder)
        
        if not notebooks:
            print("처리할 .ipynb 파일이 없습니다.")
            return
        
        print(f"\n{'='*60}")
        print(f"총 {len(notebooks)}개의 노트북 파일 발견")
        print(f"{'='*60}")
        
        for notebook in notebooks:
            self.process_notebook(notebook)
        
        # 최종 통계
        print(f"\n{'='*60}")
        print("처리 완료!")
        print(f"  처리된 노트북: {self.stats['notebooks']}개")
        print(f"  업로드된 이미지: {self.stats['images']}개")
        print(f"  에러: {self.stats['errors']}개")
        print(f"{'='*60}\n")


# 사용
if __name__ == '__main__':
    # GitHub 설정
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN 환경변수가 설정되지 않았습니다. 'export GITHUB_TOKEN=your_token' 으로 설정해주세요.")
    
    REPO_OWNER = 'ssafy-jinhyeok'
    REPO_NAME = 'AI'
    
    # 업로더 생성
    uploader = GitHubImageUploader(
        token=GITHUB_TOKEN,
        repo_owner=REPO_OWNER,
        repo_name=REPO_NAME
    )
    
    # 프로세서 생성 및 실행
    processor = NotebookImageProcessor(uploader)
    processor.process_all('.')  # 현재 폴더부터 시작