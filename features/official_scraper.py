"""
نظام متقدم لجلب معلومات المنح من المواقع الرسمية
يدعم: Beautiful Soup, Selenium, Requests, AI Parsing
"""

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScholarshipScraper:
    """فئة متقدمة لكشط معلومات المنح من المواقع الرسمية"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        })
        self.driver = None
        
    def init_selenium(self, headless=True):
        """تهيئة Selenium للصفحات الديناميكية"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("✅ تم تهيئة Selenium بنجاح")
        except Exception as e:
            logger.error(f"❌ فشل تهيئة Selenium: {e}")
            self.driver = None
    
    def close_selenium(self):
        """إغلاق Selenium"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def fetch_page(self, url: str, use_selenium: bool = False, timeout: int = 30) -> Optional[str]:
        """جلب محتوى الصفحة"""
        try:
            if use_selenium and self.driver:
                self.driver.get(url)
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                time.sleep(2)  # انتظار تحميل المحتوى الديناميكي
                return self.driver.page_source
            else:
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"❌ فشل جلب الصفحة {url}: {e}")
            return None
    
    def parse_scholarship_info(self, html: str, url: str) -> Dict:
        """تحليل معلومات المنحة من HTML"""
        soup = BeautifulSoup(html, 'lxml')
        
        # استخراج العنوان
        title = self._extract_title(soup)
        
        # استخراج الوصف
        description = self._extract_description(soup)
        
        # استخراج الدولة
        country = self._extract_country(soup, url)
        
        # استخراج التخصصات
        majors = self._extract_majors(soup)
        
        # استخراج المواعيد النهائية
        deadlines = self._extract_deadlines(soup)
        
        # استخراج متطلبات الأهلية
        eligibility = self._extract_eligibility(soup)
        
        # استخراج الفوائد والتغطية
        benefits = self._extract_benefits(soup)
        
        # استخراج متطلبات التقديم
        requirements = self._extract_requirements(soup)
        
        # استخراج رابط التقديم
        apply_link = self._extract_apply_link(soup, url)
        
        # استخراج نوع التمويل
        funding_type = self._extract_funding_type(soup)
        
        return {
            'title': title,
            'description': description,
            'country': country,
            'majors': majors,
            'deadlines': deadlines,
            'eligibility': eligibility,
            'benefits': benefits,
            'requirements': requirements,
            'apply_link': apply_link or url,
            'funding_type': funding_type,
            'source_url': url,
            'scraped_at': datetime.now().isoformat(),
            'raw_html_length': len(html)
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """استخراج عنوان المنحة"""
        # محاولة العثور على العنوان من وسم h1
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        # محاولة من عنوان الصفحة
        title_tag = soup.find('title')
        if title_tag:
            text = title_tag.get_text(strip=True)
            # تنظيف العنوان
            text = re.sub(r'\s*\|\s*.*$', '', text)
            text = re.sub(r'\s*-\s*.*$', '', text)
            return text[:200]
        
        return "منحة دراسية"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """استخراج وصف المنحة"""
        # البحث عن فقرات في المحتوى الرئيسي
        paragraphs = []
        
        # محاولة العثور على قسم "about" أو "description"
        for tag in ['p', 'div']:
            elements = soup.find_all(tag)
            for elem in elements:
                text = elem.get_text(strip=True)
                if len(text) > 100 and len(text) < 1000:
                    # تجنب النصوص القائمة على القوائم
                    if not text.startswith('•') and not text.startswith('-'):
                        paragraphs.append(text)
        
        # أخذ أول 3 فقرات ذات معنى
        meaningful = [p for p in paragraphs if any(word in p.lower() for word in 
                      ['scholarship', 'grant', 'study', 'program', 'application', 'deadline', 'eligible'])]
        
        if meaningful:
            return '\n\n'.join(meaningful[:3])
        
        return paragraphs[0] if paragraphs else "لا يوجد وصف متاح"
    
    def _extract_country(self, soup: BeautifulSoup, url: str) -> str:
        """استخراج الدولة"""
        text = soup.get_text().lower()
        
        countries_map = {
            'united states': 'الولايات المتحدة',
            'usa': 'الولايات المتحدة',
            'america': 'الولايات المتحدة',
            'united kingdom': 'المملكة المتحدة',
            'uk': 'المملكة المتحدة',
            'britain': 'المملكة المتحدة',
            'germany': 'ألمانيا',
            'france': 'فرنسا',
            'canada': 'كندا',
            'australia': 'أستراليا',
            'japan': 'اليابان',
            'china': 'الصين',
            'south korea': 'كوريا الجنوبية',
            'singapore': 'سنغافورة',
            'netherlands': 'هولندا',
            'sweden': 'السويد',
            'norway': 'النرويج',
            'denmark': 'الدنمارك',
            'finland': 'فنلندا',
            'switzerland': 'سويسرا',
            'italy': 'إيطاليا',
            'spain': 'إسبانيا',
            'turkey': 'تركيا',
            'egypt': 'مصر',
            'saudi arabia': 'السعودية',
            'uae': 'الإمارات',
            'qatar': 'قطر',
            'kuwait': 'الكويت',
            'malaysia': 'ماليزيا',
            'india': 'الهند',
            'russia': 'روسيا',
            'poland': 'بولندا',
            'hungary': 'هنغاريا',
            'romania': 'رومانيا',
            'czech republic': 'جمهورية التشيك',
            'austria': 'النمسا',
            'belgium': 'بلجيكا',
            'ireland': 'أيرلندا',
            'new zealand': 'نيوزيلندا',
            'south africa': 'جنوب أفريقيا',
            'brazil': 'البرازيل',
            'mexico': 'المكسيك',
            'argentina': 'الأرجنتين',
            'chile': 'تشيلي',
            'colombia': 'كولومبيا',
            'israel': 'إسرائيل',
            'jordan': 'الأردن',
            'lebanon': 'لبنان',
            'morocco': 'المغرب',
            'tunisia': 'تونس',
            'algeria': 'الجزائر',
            'libya': 'ليبيا',
            'iraq': 'العراق',
            'pakistan': 'باكستان',
            'bangladesh': 'بنغلاديش',
            'indonesia': 'إندونيسيا',
            'thailand': 'تايلاند',
            'vietnam': 'فيتنام',
            'philippines': 'الفلبين',
            'kazakhstan': 'كازاخستان',
            'uzbekistan': 'أوزبكستان',
            'georgia': 'جورجيا',
            'armenia': 'أرمينيا',
            'azerbaijan': 'أذربيجان',
            'ukraine': 'أوكرانيا',
            'belarus': 'بيلاروسيا',
            'estonia': 'إستونيا',
            'latvia': 'لاتفيا',
            'lithuania': 'ليتوانيا',
            'croatia': 'كرواتيا',
            'serbia': 'صربيا',
            'bulgaria': 'بلغاريا',
            'greece': 'اليونان',
            'portugal': 'البرتغال',
            'luxembourg': 'لوكسمبورغ',
            'iceland': 'آيسلندا',
            'malta': 'مالطا',
            'cyprus': 'قبرص'
        }
        
        for key, value in countries_map.items():
            if key in text:
                return value
        
        # محاولة من URL
        url_lower = url.lower()
        for key, value in countries_map.items():
            if f'.{key}/' in url_lower or f'/{key}/' in url_lower:
                return value
        
        return "دولة غير محددة"
    
    def _extract_majors(self, soup: BeautifulSoup) -> List[str]:
        """استخراج التخصصات المتاحة"""
        majors = set()
        text = soup.get_text()
        
        # قائمة بالتخصصات الشائعة
        common_majors = [
            'computer science', 'علوم الحاسوب', 'information technology', 'تكنولوجيا المعلومات',
            'engineering', 'الهندسة', 'mechanical engineering', 'الهندسة الميكانيكية',
            'electrical engineering', 'الهندسة الكهربائية', 'civil engineering', 'الهندسة المدنية',
            'business administration', 'إدارة الأعمال', 'mba', 'ماجستير إدارة الأعمال',
            'medicine', 'الطب', 'nursing', 'التمريض', 'pharmacy', 'الصيدلة',
            'dentistry', 'طب الأسنان', 'veterinary medicine', 'الطب البيطري',
            'law', 'القانون', 'international relations', 'العلاقات الدولية',
            'political science', 'العلوم السياسية', 'economics', 'الاقتصاد',
            'finance', 'المالية', 'accounting', 'المحاسبة', 'marketing', 'التسويق',
            'psychology', 'علم النفس', 'sociology', 'علم الاجتماع',
            'education', 'التربية', 'teaching', 'التدريس',
            'mathematics', 'الرياضيات', 'physics', 'الفيزياء', 'chemistry', 'الكيمياء',
            'biology', 'الأحياء', 'environmental science', 'العلوم البيئية',
            'architecture', 'العمارة', 'design', 'التصميم', 'art', 'الفنون',
            'literature', 'الأدب', 'linguistics', 'اللغويات', 'translation', 'الترجمة',
            'journalism', 'الصحافة', 'media', 'الإعلام', 'communication', 'الاتصالات',
            'agriculture', 'الزراعة', 'food science', 'علوم الأغذية',
            'public health', 'الصحة العامة', 'epidemiology', 'علم الأوبئة',
            'data science', 'علوم البيانات', 'artificial intelligence', 'الذكاء الاصطناعي',
            'machine learning', 'تعلم الآلة', 'cybersecurity', 'الأمن السيبراني',
            'renewable energy', 'الطاقة المتجددة', 'sustainability', 'الاستدامة',
            'biotechnology', 'التكنولوجيا الحيوية', 'nanotechnology', 'تكنولوجيا النانو',
            'aerospace engineering', 'هندسة الفضاء', 'petroleum engineering', 'هندسة البترول',
            'marine biology', 'الأحياء البحرية', 'geology', 'الجيولوجيا',
            'anthropology', 'الأنثروبولوجيا', 'history', 'التاريخ', 'philosophy', 'الفلسفة',
            'theology', 'اللاهوت', 'islamic studies', 'الدراسات الإسلامية',
            'sharia', 'الشريعة', 'human rights', 'حقوق الإنسان',
            'development studies', 'دراسات التنمية', 'urban planning', 'التخطيط الحضري',
            'logistics', 'اللوجستيات', 'supply chain', 'سلسلة التوريد',
            'hospitality management', 'إدارة الضيافة', 'tourism', 'السياحة',
            'sports science', 'علوم الرياضة', 'physical education', 'التربية الرياضية',
            'music', 'الموسيقى', 'film', 'السينما', 'photography', 'التصوير الفوتوغرافي',
            'fashion design', 'تصميم الأزياء', 'interior design', 'تصميم الداخلي',
            'graphic design', 'التصميم الجرافيكي', 'game design', 'تصميم الألعاب',
            'nutrition', 'التغذية', 'dietetics', 'علم التغذية',
            'occupational therapy', 'العلاج الوظيفي', 'physical therapy', 'العلاج الطبيعي',
            'speech therapy', 'علاج النطق', 'social work', 'العمل الاجتماعي',
            'library science', 'علم المكتبات', 'archival science', 'علم الأرشيف',
            'museum studies', 'دراسات المتاحف', 'cultural studies', 'الدراسات الثقافية',
            'gender studies', 'دراسات النوع الاجتماعي', 'ethnic studies', 'دراسات الأعراق',
            'area studies', 'دراسات المناطق', 'middle eastern studies', 'دراسات الشرق الأوسط',
            'asian studies', 'الدراسات الآسيوية', 'european studies', 'الدراسات الأوروبية',
            'american studies', 'الدراسات الأمريكية', 'african studies', 'الدراسات الأفريقية'
        ]
        
        text_lower = text.lower()
        for major in common_majors:
            if major.lower() in text_lower:
                majors.add(major)
        
        return list(majors) if majors else ["تخصصات متعددة"]
    
    def _extract_deadlines(self, soup: BeautifulSoup) -> List[str]:
        """استخراج المواعيد النهائية"""
        deadlines = []
        text = soup.get_text()
        
        # أنماط التواريخ الشائعة
        date_patterns = [
            r'\b(\d{1,2})\s*(?:st|nd|rd|th)?\s*(january|february|march|april|may|june|july|august|september|october|november|december)\s*(\d{4})\b',
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s*(\d{1,2}),?\s*(\d{4})\b',
            r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',
            r'\b(\d{4})-(\d{2})-(\d{2})\b',
            r'\b(deadline|closing date|application deadline|last date)\s*[:\-]?\s*(.+?)(?:\n|$)',
            r'\b(موعد نهائي|آخر موعد|تاريخ الإغلاق)\s*[:\-]?\s*(.+?)(?:\n|$)'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    deadline_str = ' '.join(str(m) for m in match)
                else:
                    deadline_str = str(match)
                
                if len(deadline_str) > 5 and len(deadline_str) < 100:
                    deadlines.append(deadline_str.strip())
        
        return deadlines[:5] if deadlines else ["مواعيد غير محددة"]
    
    def _extract_eligibility(self, soup: BeautifulSoup) -> List[str]:
        """استخراج متطلبات الأهلية"""
        eligibility = []
        
        # كلمات مفتاحية للأهلية
        keywords = [
            'eligible', 'eligibility', 'requirements', 'qualifications', 'criteria',
            'must have', 'should have', 'required', 'minimum', 'Bachelor', 'Master',
            'PhD', 'GPA', 'grade', 'age', 'nationality', 'citizen', 'resident',
            'مرشح', 'شروط', 'متطلبات', 'أهلية', 'مؤهل', 'بكالوريوس', 'ماجستير',
            'دكتوراه', 'معدل', 'عمر', 'جنسية', 'درجة', 'شهادة'
        ]
        
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text(strip=True)
            if any(keyword.lower() in text.lower() for keyword in keywords):
                if len(text) > 20 and len(text) < 500:
                    eligibility.append(text)
        
        return eligibility[:10] if eligibility else ["شروط عامة للتقديم"]
    
    def _extract_benefits(self, soup: BeautifulSoup) -> List[str]:
        """استخراج الفوائد والتغطية"""
        benefits = []
        
        keywords = [
            'fully funded', 'partially funded', 'covers', 'coverage', 'benefits',
            'stipend', 'allowance', 'salary', 'tuition', 'accommodation', 'housing',
            'travel', 'flight', 'insurance', 'health', 'visa', 'monthly',
            'ممولة بالكامل', 'ممولة جزئياً', 'تغطي', 'تغطية', 'فوائد', 'منحة',
            'راتب', 'بدل', 'سكن', 'إقامة', 'تذكرة', 'تأمين', 'شهري', 'سنوي'
        ]
        
        # البحث عن قوائم
        for li in soup.find_all('li'):
            text = li.get_text(strip=True)
            if any(keyword.lower() in text.lower() for keyword in keywords):
                if len(text) > 10 and len(text) < 300:
                    benefits.append(text)
        
        # البحث عن فقرات
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text(strip=True)
            if any(keyword.lower() in text.lower() for keyword in keywords):
                if len(text) > 20 and len(text) < 500:
                    benefits.append(text)
        
        return benefits[:10] if benefits else ["تفاصيل التمويل متاحة على الموقع الرسمي"]
    
    def _extract_requirements(self, soup: BeautifulSoup) -> List[str]:
        """استخراج متطلبات التقديم"""
        requirements = []
        
        keywords = [
            'documents', 'required documents', 'application documents', 'submit',
            'transcript', 'certificate', 'recommendation', 'reference', 'CV', 'resume',
            'motivation letter', 'statement of purpose', 'essay', 'proposal',
            'IELTS', 'TOEFL', 'English', 'language proficiency', 'passport',
            'وثائق', 'مستندات', 'شهادة', 'توصية', 'سيرة ذاتية', 'خطاب',
            'мотивационное', 'بيان', 'بحث', 'ايلتس', 'توفل', 'لغة', 'جواز سفر'
        ]
        
        lists = soup.find_all(['ul', 'ol'])
        for lst in lists:
            for li in lst.find_all('li'):
                text = li.get_text(strip=True)
                if any(keyword.lower() in text.lower() for keyword in keywords):
                    if len(text) > 10 and len(text) < 300:
                        requirements.append(text)
        
        return requirements[:15] if requirements else ["الوثائق المطلوبة مذكورة على الموقع الرسمي"]
    
    def _extract_apply_link(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """استخراج رابط التقديم"""
        # البحث عن أزرار التقديم
        apply_keywords = ['apply', 'application', 'submit', 'register', 'enroll', 'قدم', 'تقديم', 'سجل']
        
        for a in soup.find_all('a', href=True):
            text = a.get_text(strip=True).lower()
            href = a['href'].lower()
            
            if any(keyword in text or keyword in href for keyword in apply_keywords):
                full_url = href if href.startswith('http') else url.split('/')[0] + '//' + url.split('/')[2] + href
                return full_url
        
        return url
    
    def _extract_funding_type(self, soup: BeautifulSoup) -> str:
        """استخراج نوع التمويل"""
        text = soup.get_text().lower()
        
        if any(phrase in text for phrase in ['fully funded', 'full scholarship', '100%', 'complete funding', 'ممولة بالكامل']):
            return "ممولة بالكامل"
        elif any(phrase in text for phrase in ['partially funded', 'partial scholarship', '50%', '部分资助', 'ممولة جزئياً']):
            return "ممولة جزئياً"
        elif any(phrase in text for phrase in ['self-funded', 'tuition only', 'بدون تمويل']):
            return "غير ممولة"
        else:
            return "نوع التمويل غير محدد"
    
    def scrape_scholarship(self, url: str, use_selenium: bool = False) -> Optional[Dict]:
        """الدالة الرئيسية لكشط معلومات المنحة"""
        logger.info(f"🔍 جاري كشط معلومات المنحة من: {url}")
        
        html = self.fetch_page(url, use_selenium=use_selenium)
        if not html:
            return None
        
        info = self.parse_scholarship_info(html, url)
        
        logger.info(f"✅ تم كشط معلومات المنحة بنجاح: {info['title']}")
        return info


class OfficialSourcesScraper:
    """كاشط متخصص للمواقع الرسمية للمنح"""
    
    def __init__(self):
        self.scraper = ScholarshipScraper()
        
        # قائمة بالمواقع الرسمية الشهيرة
        self.official_sources = {
            'erasmus_plus': {
                'base_url': 'https://erasmus-plus.ec.europa.eu',
                'search_urls': [
                    'https://erasmus-plus.ec.europa.eu/opportunities',
                    'https://erasmus-plus.ec.europa.eu/opportunities/opportunities-for-individuals/students'
                ],
                'region': 'Europe'
            },
            'chevening': {
                'base_url': 'https://www.chevening.org',
                'search_urls': [
                    'https://www.chevening.org/scholarships'
                ],
                'region': 'UK'
            },
            'fulbright': {
                'base_url': 'https://foreign.fulbrightonline.org',
                'search_urls': [
                    'https://foreign.fulbrightonline.org/home'
                ],
                'region': 'USA'
            },
            'daad': {
                'base_url': 'https://www.daad.de',
                'search_urls': [
                    'https://www.daad.de/en/study-and-research-in-germany/scholarships'
                ],
                'region': 'Germany'
            },
            'campus_france': {
                'base_url': 'https://www.campusfrance.org',
                'search_urls': [
                    'https://www.campusfrance.org/en/scholarships'
                ],
                'region': 'France'
            },
            'mext': {
                'base_url': 'https://www.studyinjapan.go.jp',
                'search_urls': [
                    'https://www.studyinjapan.go.jp/en/_mt/applications/scholarships'
                ],
                'region': 'Japan'
            },
            'csc': {
                'base_url': 'https://www.campuschina.org',
                'search_urls': [
                    'https://www.campuschina.org/content/details3_75778.html'
                ],
                'region': 'China'
            },
            'study_in_egypt': {
                'base_url': 'https://studyinegypt.gov.eg',
                'search_urls': [
                    'https://studyinegypt.gov.eg/scholarships'
                ],
                'region': 'Egypt'
            },
            'tudors': {
                'base_url': 'https://www.tudors.ro',
                'search_urls': [
                    'https://www.tudors.ro/scholarships'
                ],
                'region': 'Romania'
            },
            'stipendium_hungaricum': {
                'base_url': 'https://stipendiumhungaricum.hu',
                'search_urls': [
                    'https://stipendiumhungaricum.hu'
                ],
                'region': 'Hungary'
            }
        }
    
    def scrape_from_source(self, source_name: str) -> List[Dict]:
        """كشط المنح من مصدر رسمي محدد"""
        if source_name not in self.official_sources:
            logger.error(f"❌ المصدر {source_name} غير موجود")
            return []
        
        source = self.official_sources[source_name]
        scholarships = []
        
        for url in source['search_urls']:
            info = self.scraper.scrape_scholarship(url, use_selenium=True)
            if info:
                info['source_name'] = source_name
                info['region'] = source['region']
                scholarships.append(info)
        
        return scholarships
    
    def scrape_all_sources(self) -> List[Dict]:
        """كشط المنح من جميع المصادر الرسمية"""
        all_scholarships = []
        
        for source_name in self.official_sources:
            logger.info(f"📊 جاري الكشط من {source_name}...")
            scholarships = self.scrape_from_source(source_name)
            all_scholarships.extend(scholarships)
            time.sleep(2)  # تأخير لتجنب الحظر
        
        return all_scholarships
    
    def get_available_sources(self) -> List[str]:
        """الحصول على قائمة المصادر المتاحة"""
        return list(self.official_sources.keys())


# دوال مساعدة للاستخدام في البوت
def get_scholarship_details(url: str) -> Dict:
    """الحصول على تفاصيل منحة من رابط معين"""
    scraper = ScholarshipScraper()
    result = scraper.scrape_scholarship(url, use_selenium=True)
    scraper.close_selenium()
    return result or {'error': 'فشل في جلب التفاصيل'}


def search_official_scholarships(country: str = None, major: str = None) -> List[Dict]:
    """البحث عن منح في المصادر الرسمية حسب الدولة والتخصص"""
    official_scraper = OfficialSourcesScraper()
    all_scholarships = official_scraper.scrape_all_sources()
    
    filtered = []
    for sch in all_scholarships:
        match = True
        
        if country and country.lower() not in sch.get('country', '').lower():
            match = False
        
        if major and not any(major.lower() in m.lower() for m in sch.get('majors', [])):
            match = False
        
        if match:
            filtered.append(sch)
    
    return filtered


if __name__ == "__main__":
    # مثال للاستخدام
    print("🚀 بدء نظام كشط المنح المتقدم")
    
    # اختبار كشط منحة واحدة
    test_url = "https://www.chevening.org/scholarships"
    details = get_scholarship_details(test_url)
    
    if 'error' not in details:
        print(f"\n✅ تم العثور على المنحة: {details.get('title', 'غير معروف')}")
        print(f"🌍 الدولة: {details.get('country', 'غير محدد')}")
        print(f"📚 التخصصات: {', '.join(details.get('majors', [])[:5])}")
        print(f"💰 نوع التمويل: {details.get('funding_type', 'غير محدد')}")
        print(f"🔗 رابط التقديم: {details.get('apply_link', test_url)}")
    else:
        print(f"❌ خطأ: {details['error']}")
    
    print("\n✨ انتهى الاختبار")
