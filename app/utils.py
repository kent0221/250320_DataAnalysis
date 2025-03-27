def extract_video_id(url):
    """
    TikTok動画URLからIDを抽出する
    
    Args:
        url: TikTok動画URL
        
    Returns:
        抽出した動画ID、抽出できない場合はそのままURLを返す
    """
    # 1. URLから直接IDを抽出する試み
    import re
    match = re.search(r'video/(\d+)', url)
    if match:
        return match.group(1)
    
    # 2. 数字のみの場合はそのままIDとして返す
    if url.isdigit():
        return url
    
    # 抽出できない場合はそのまま返す
    return url 