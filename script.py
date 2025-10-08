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
        self.processed_base64 = set()  # 이미 처리된 BASE64 문자열 추적
    
    def generate_hash_filename(self, base64_string):
        """BASE64 문자열의 해시값으로 파일명 생성"""
        hash_hex = hashlib.sha256(base64_string.encode()).hexdigest()[:16]
        return f"{hash_hex}.png"
    
    def find_notebooks(self, base_folder='.'):
        """모든 .ipynb 파일 찾기"""
        notebooks = []
        for root, dirs, files in os.walk(base_folder):
            dirs[:] = [d for d in dirs if d != '.ipynb_checkpoints']
            for file in files:
                if file.endswith('.ipynb'):
                    notebooks.append(os.path.join(root, file))
        return notebooks
    
    def process_notebook(self, notebook_path):
        """노트북 파일의 BASE64 이미지를 찾아서 업로드 후 치환"""
        print(f"\n처리 중: {notebook_path}")
        self.processed_base64.clear()  # 노트북마다 초기화
        
        try:
            with open(notebook_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            replaced_count = 0
            
            # 1. data:image/png;base64, 형식 처리
            pattern_data_uri = r'data:image/(png|jpeg|jpg);base64,([A-Za-z0-9+/]{200,}={0,2})'
            data_uri_matches = re.findall(pattern_data_uri, content)
            
            if data_uri_matches:
                print(f"  발견된 data URI 이미지: {len(data_uri_matches)}개")
                unique_data_uri = list(set(data_uri_matches))
                
                for idx, (img_type, base64_str) in enumerate(unique_data_uri, 1):
                    if base64_str in self.processed_base64:
                        continue
                    
                    try:
                        filename = self.generate_hash_filename(base64_str)
                        github_path = f"{self.image_folder}/{filename}"
                        
                        print(f"  [Data URI {idx}/{len(unique_data_uri)}] 업로드: {filename}...", end=' ')
                        
                        url = self.uploader.upload_base64_image(base64_str, github_path)
                        
                        # data:image/png;base64,xxx 전체를 URL로 치환
                        old_data_uri = f'data:image/{img_type};base64,{base64_str}'
                        content = content.replace(old_data_uri, url)
                        
                        self.processed_base64.add(base64_str)
                        replaced_count += 1
                        self.stats['images'] += 1
                        
                        print(f"✓")
                        time.sleep(0.5)
                        
                    except Exception as e:
                        print(f"✗ ({str(e)})")
                        self.stats['errors'] += 1
            
            # 2. 순수 BASE64 문자열 처리 (따옴표로 둘러싸인)
            pattern_pure_base64 = r'"([A-Za-z0-9+/]{200,}={0,2})"'
            pure_matches = re.findall(pattern_pure_base64, content)
            
            if pure_matches:
                # 이미 처리되지 않은 것만 필터링
                unprocessed = [m for m in pure_matches if m not in self.processed_base64]
                
                if unprocessed:
                    print(f"  발견된 순수 BASE64 문자열: {len(unprocessed)}개")
                    unique_pure = list(set(unprocessed))
                    
                    for idx, base64_str in enumerate(unique_pure, 1):
                        try:
                            filename = self.generate_hash_filename(base64_str)
                            github_path = f"{self.image_folder}/{filename}"
                            
                            print(f"  [순수 BASE64 {idx}/{len(unique_pure)}] 업로드: {filename}...", end=' ')
                            
                            url = self.uploader.upload_base64_image(base64_str, github_path)
                            
                            # "base64_string"을 "url"로 치환
                            content = content.replace(f'"{base64_str}"', f'"{url}"')
                            
                            self.processed_base64.add(base64_str)
                            replaced_count += 1
                            self.stats['images'] += 1
                            
                            print(f"✓")
                            time.sleep(0.5)
                            
                        except Exception as e:
                            print(f"✗ ({str(e)})")
                            self.stats['errors'] += 1
            
            if replaced_count > 0:
                with open(notebook_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✓ 완료: {replaced_count}개 이미지 업로드 및 치환")
                self.stats['notebooks'] += 1
            else:
                print("  - 처리할 이미지 없음")
            
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
        
        print(f"\n{'='*60}")
        print("처리 완료!")
        print(f"  처리된 노트북: {self.stats['notebooks']}개")
        print(f"  업로드된 이미지: {self.stats['images']}개")
        print(f"  에러: {self.stats['errors']}개")
        print(f"{'='*60}\n")


# 사용
if __name__ == '__main__':
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN 환경변수가 설정되지 않았습니다. 'export GITHUB_TOKEN=your_token' 으로 설정해주세요.")
    
    REPO_OWNER = 'ssafy-jinhyeok'
    REPO_NAME = 'AI'
    
    uploader = GitHubImageUploader(
        token=GITHUB_TOKEN,
        repo_owner=REPO_OWNER,
        repo_name=REPO_NAME
    )
    
    processor = NotebookImageProcessor(uploader)
    processor.process_all('.')