import requests
import pandas as pd
import time
from datetime import datetime
import json
import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional, Set
from pathlib import Path

class RocketReachExtractor:
    def __init__(self, api_key: str, history_file: str = "contact_history.json"):
        """Initialize the RocketReach API client"""
        self.api_key = api_key
        self.base_url = "https://api.rocketreach.co/v2/api"
        self.headers = {
            "Api-Key": api_key,
            "Content-Type": "application/json"
        }

        # Rate limit tracking with multiple time windows
        # Actual limits from your RocketReach account:
        # Searches: 15/min, 50/hour, 500/day, 10000/month
        # Lookups: 15/min, 100/hour, 500/day, 5000/month
        self.lookup_calls = []
        self.search_calls = []

        # Rate limits for lookups (person_lookup)
        self.lookup_rate_limits = {
            'minute': {'limit': 15, 'window': 60},
            'hour': {'limit': 100, 'window': 3600},
            'day': {'limit': 500, 'window': 86400},
            'month': {'limit': 5000, 'window': 2592000}
        }

        # Rate limits for searches (person_search)
        self.search_rate_limits = {
            'minute': {'limit': 15, 'window': 60},
            'hour': {'limit': 50, 'window': 3600},
            'day': {'limit': 500, 'window': 86400},
            'month': {'limit': 10000, 'window': 2592000}
        }

        # Duplicate tracking
        self.history_file = history_file
        self.contacted_ids = self._load_contact_history()

        # Sector classification keywords
        self.sector_keywords = {
            "Investment Banking": [
                "investment bank", "goldman sachs", "morgan stanley", "jp morgan", "jpmorgan",
                "bank of america merrill", "merrill lynch", "citi", "citigroup", "barclays",
                "credit suisse", "ubs", "deutsche bank", "jefferies", "lazard", "evercore",
                "rothschild", "moelis", "centerview", "pjt partners", "greenhill", "houlihan lokey",
                "investment banking", "m&a", "mergers and acquisitions", "capital markets", "ibd"
            ],
            "Consulting": [
                "mckinsey", "bain", "boston consulting", "bcg", "deloitte consulting",
                "pwc consulting", "accenture", "kpmg consulting", "ey consulting", "parthenon",
                "oliver wyman", "strategy&", "roland berger", "a.t. kearney", "l.e.k",
                "consultant", "management consulting", "strategy consulting"
            ],
            "Hedge Fund": [
                "hedge fund", "bridgewater", "citadel", "millennium", "point72", "two sigma",
                "d.e. shaw", "renaissance technologies", "elliott management", "tiger global",
                "coatue", "viking global", "baupost", "appaloosa", "third point", "och-ziff",
                "paulson", "soros fund", "quantitative", "long short", "macro fund"
            ],
            "Private Equity": [
                "private equity", "blackstone", "kkr", "carlyle", "apollo", "tpg", "warburg pincus",
                "bain capital", "vista equity", "silver lake", "thoma bravo", "advent", "permira",
                "cvc", "apax", "general atlantic", "hellman & friedman", "providence equity",
                "buyout", "growth equity", "leveraged buyout", "lbo"
            ],
            "Venture Capital": [
                "venture capital", "sequoia", "andreessen horowitz", "a16z", "accel", "benchmark",
                "greylock", "kleiner perkins", "lightspeed", "insight partners", "nea", "khosla",
                "founders fund", "general catalyst", "bessemer", "index ventures", "ycombinator",
                "y combinator", "500 startups", "techstars", "seed", "series a", "series b"
            ]
        }
    
    def _load_contact_history(self) -> Set[str]:
        """Load previously contacted person IDs from history file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get("contacted_ids", []))
            except Exception as e:
                print(f"Warning: Could not load contact history: {e}")
                return set()
        return set()

    def _save_contact_history(self) -> None:
        """Save contacted person IDs to history file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump({"contacted_ids": list(self.contacted_ids)}, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save contact history: {e}")

    def _is_duplicate(self, person_id: str, linkedin_url: str = None) -> bool:
        """Check if this person has already been contacted"""
        # Check by person ID
        if str(person_id) in self.contacted_ids:
            return True
        # Also check by LinkedIn URL if available
        if linkedin_url and linkedin_url in self.contacted_ids:
            return True
        return False

    def _mark_as_contacted(self, person_id: str, linkedin_url: str = None) -> None:
        """Mark a person as contacted"""
        self.contacted_ids.add(str(person_id))
        if linkedin_url:
            self.contacted_ids.add(linkedin_url)
        self._save_contact_history()

    def _classify_sector(self, title: str, company: str) -> str:
        """Classify the person's sector based on title and company"""
        text = f"{title} {company}".lower()

        # Check each sector's keywords
        for sector, keywords in self.sector_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return sector

        return "Other"

    def get_rate_limit_status(self) -> Dict[str, Dict[str, int]]:
        """
        Get current rate limit usage across all time windows

        Returns:
            Dict with 'lookup' and 'search' usage stats
        """
        current_time = time.time()
        status = {}

        # Lookup status
        status['lookup'] = {}
        for window_name, config in self.lookup_rate_limits.items():
            window_seconds = config['window']
            limit = config['limit']
            recent_calls = len([t for t in self.lookup_calls if current_time - t < window_seconds])
            status['lookup'][window_name] = {
                'used': recent_calls,
                'limit': limit,
                'remaining': limit - recent_calls
            }

        # Search status
        status['search'] = {}
        for window_name, config in self.search_rate_limits.items():
            window_seconds = config['window']
            limit = config['limit']
            recent_calls = len([t for t in self.search_calls if current_time - t < window_seconds])
            status['search'][window_name] = {
                'used': recent_calls,
                'limit': limit,
                'remaining': limit - recent_calls
            }

        return status

    def _check_rate_limit(self, call_type: str) -> None:
        """
        Check and enforce rate limits across multiple time windows
        Lookups: 15/min, 100/hour, 500/day, 5000/month
        Searches: 15/min, 50/hour, 500/day, 10000/month
        """
        current_time = time.time()
        calls = self.search_calls if call_type == "search" else self.lookup_calls
        rate_limits = self.search_rate_limits if call_type == "search" else self.lookup_rate_limits

        # Check each time window
        for window_name, config in rate_limits.items():
            limit = config['limit']
            window_seconds = config['window']

            # Remove calls older than this window
            recent_calls = [t for t in calls if current_time - t < window_seconds]

            # If we've hit the limit for this window, wait
            if len(recent_calls) >= limit:
                oldest_call = min(recent_calls)
                wait_time = window_seconds - (current_time - oldest_call) + 1

                print(f"⏳ Rate limit reached: {limit} calls per {window_name}")
                print(f"   Waiting {wait_time:.1f} seconds before next call...")

                time.sleep(wait_time)

                # After waiting, clean up old calls and recheck
                current_time = time.time()
                calls[:] = [t for t in calls if current_time - t < window_seconds]

        # Clean up all old calls (older than the longest window)
        max_window = max(config['window'] for config in rate_limits.values())
        calls[:] = [t for t in calls if current_time - t < max_window]

        # Record this call
        calls.append(current_time)
    
    def search_people(self, search_params: Dict) -> List[Dict]:
        """
        Search for people based on criteria

        Example search_params:
        {
            "query": {
                "current_title": ["Software Engineer", "Developer"],
                "current_employer": ["Google", "Microsoft"],
                "location": ["San Francisco, CA"]
            },
            "page_size": 100,
            "start": 1
        }
        """
        self._check_rate_limit("search")

        url = f"{self.base_url}/person/search"

        # Clean up search params - remove empty arrays/values
        cleaned_params = {"query": {}}
        if "query" in search_params:
            for key, value in search_params["query"].items():
                if value and len(value) > 0:  # Only include non-empty values
                    cleaned_params["query"][key] = value

        # Validate that at least one search parameter is provided
        if not cleaned_params["query"]:
            print("Error: At least one search parameter is required (e.g., current_employer, current_title, location)")
            return []

        # Add pagination params
        if "page_size" in search_params:
            cleaned_params["page_size"] = search_params["page_size"]
        if "start" in search_params:
            cleaned_params["start"] = search_params["start"]

        try:
            response = requests.post(url, headers=self.headers, json=cleaned_params)
            response.raise_for_status()
            data = response.json()

            return data.get("profiles", [])

        except requests.exceptions.RequestException as e:
            print(f"Search error: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return []
    
    def lookup_person(self, person_id: Optional[int] = None, name: Optional[str] = None,
                     current_employer: Optional[str] = None, linkedin_url: Optional[str] = None) -> Dict:
        """
        Lookup detailed contact information for a person
        Can use person_id from search results, or name + employer, or LinkedIn URL
        """
        self._check_rate_limit("lookup")

        url = f"{self.base_url}/person/lookup"
        
        params = {}
        if person_id:
            params["id"] = person_id
        elif linkedin_url:
            params["linkedin_url"] = linkedin_url
        elif name and current_employer:
            params["name"] = name
            params["current_employer"] = current_employer
        else:
            print("Error: Need either person_id, linkedin_url, or name+employer")
            return {}

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Lookup error: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return {}
    
    def extract_all_contacts(self, search_params: Dict, max_results: int = 500) -> pd.DataFrame:
        """
        Main function: Search for people and get all their contact info
        Returns a DataFrame with all emails and their confidence scores
        
        Press Ctrl+C at any time to stop and save progress
        """
        all_contacts = []
        page_size = 100
        current_start = 1
        total_fetched = 0
        
        print(f"Starting contact extraction (max {max_results} results)...")
        print("Press Ctrl+C at any time to stop and save your progress\n")
        
        try:
            # Search phase
            while total_fetched < max_results:
                search_params["page_size"] = min(page_size, max_results - total_fetched)
                search_params["start"] = current_start
                
                print(f"Searching page {current_start} (fetched {total_fetched} so far)...")
                profiles = self.search_people(search_params)
                
                if not profiles:
                    if total_fetched == 0:
                        print("\n⚠️  ERROR: No results found for your search criteria.")
                        print("Suggestions:")
                        print("  - Broaden your search parameters")
                        print("  - Check spelling of company names, titles, or schools")
                        print("  - Try removing some filters\n")
                        return pd.DataFrame()  # Return empty DataFrame
                    else:
                        print("No more results found.")
                        break
                
                # Lookup phase - get detailed contact info for each profile
                for i, profile in enumerate(profiles):
                    person_id = profile.get("id")
                    name = profile.get("name", "Unknown")
                    linkedin_url = profile.get("linkedin_url", "")

                    # Check for duplicates
                    if self._is_duplicate(person_id, linkedin_url):
                        print(f"  Skipping {name} ({i+1}/{len(profiles)}) - Already contacted")
                        continue

                    print(f"  Fetching contacts for {name} ({i+1}/{len(profiles)})...")

                    contact_details = self.lookup_person(person_id=person_id)
                    
                    if contact_details:
                        # Parse the contact information
                        contact_entry = self._parse_contact_data(profile, contact_details)
                        all_contacts.append(contact_entry)

                        # Mark as contacted to avoid duplicates in future runs
                        self._mark_as_contacted(person_id, linkedin_url)
                    
                    time.sleep(0.5)  # Small delay between lookups
                
                total_fetched += len(profiles)
                current_start += len(profiles)
                
                # Check if we got fewer results than requested (last page)
                if len(profiles) < page_size:
                    break
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Process interrupted by user (Ctrl+C)")
            print(f"Saving {len(all_contacts)} contacts collected so far...")
        
        if len(all_contacts) == 0:
            print("\n⚠️  No contacts were successfully extracted.")
            return pd.DataFrame()
        
        print(f"\n✓ Completed! Extracted {len(all_contacts)} contacts.")
        
        # Convert to DataFrame
        return pd.DataFrame(all_contacts)
    
    def _parse_contact_data(self, profile: Dict, contact_details: Dict) -> Dict:
        """Parse and structure contact data"""
        # Extract name components
        full_name = profile.get("name", "")
        name_parts = full_name.split()
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        # Classify sector
        current_title = profile.get("current_title", "")
        current_employer = profile.get("current_employer", "")
        sector = self._classify_sector(current_title, current_employer)

        # Base info
        entry = {
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "current_title": current_title,
            "current_employer": current_employer,
            "sector": sector,
            "location": profile.get("location", ""),
            "linkedin_url": profile.get("linkedin_url", ""),
        }
        
        # Extract all emails with confidence scores
        emails = contact_details.get("emails", [])
        for idx, email_obj in enumerate(emails[:5]):  # Limit to top 5 emails
            email_num = idx + 1
            entry[f"email_{email_num}"] = email_obj.get("email", "")
            entry[f"email_{email_num}_status"] = email_obj.get("status", "")
            entry[f"email_{email_num}_type"] = email_obj.get("type", "")
        
        # Extract phone numbers
        phones = contact_details.get("phones", [])
        for idx, phone_obj in enumerate(phones[:3]):  # Limit to top 3 phones
            phone_num = idx + 1
            entry[f"phone_{phone_num}"] = phone_obj.get("number", "")
            entry[f"phone_{phone_num}_type"] = phone_obj.get("type", "")
        
        return entry
    
    def send_email_outlook(self, to_email: str, to_name: str, subject: str, body: str,
                          sender_email: str, sender_password: str) -> bool:
        """
        Send an email via Outlook/Office 365 SMTP

        Args:
            to_email: Recipient's email address
            to_name: Recipient's name (for personalization)
            subject: Email subject
            body: Email body (can include HTML)
            sender_email: Your u.nus.edu email address
            sender_password: Your email password or app-specific password

        Returns:
            bool: True if email sent successfully, False otherwise

        Note: For u.nus.edu emails, you may need to generate an app-specific password
        from your Microsoft account settings if 2FA is enabled.
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = sender_email
            msg['To'] = to_email
            msg['Subject'] = subject

            # Personalize the body with recipient's name
            personalized_body = body.replace("{name}", to_name.split()[0])

            # Attach both plain text and HTML versions
            text_part = MIMEText(personalized_body, 'plain')
            html_part = MIMEText(personalized_body, 'html')

            msg.attach(text_part)
            msg.attach(html_part)

            # Office 365 SMTP settings
            smtp_server = "smtp.office365.com"
            smtp_port = 587

            # Connect and send
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)

            print(f"  ✓ Email sent to {to_name} ({to_email})")
            return True

        except Exception as e:
            print(f"  ✗ Failed to send email to {to_name}: {e}")
            return False

    def send_bulk_emails(self, contacts_df: pd.DataFrame, email_template: str,
                        subject_template: str, sender_email: str, sender_password: str,
                        email_column: str = "email_1") -> Dict[str, int]:
        """
        Send personalized emails to all contacts in the DataFrame

        Args:
            contacts_df: DataFrame containing contact information
            email_template: Email body template (use {name} for first name)
            subject_template: Email subject template (use {name} for first name)
            sender_email: Your u.nus.edu email
            sender_password: Your email password
            email_column: Which email column to use (default: email_1)

        Returns:
            Dict with 'sent' and 'failed' counts
        """
        results = {"sent": 0, "failed": 0}

        print(f"\nStarting to send {len(contacts_df)} emails...")
        print("=" * 60)

        for idx, row in contacts_df.iterrows():
            to_email = row.get(email_column, "")
            to_name = row.get("full_name", "Unknown")
            first_name = row.get("first_name", to_name.split()[0])

            if not to_email or pd.isna(to_email):
                print(f"  ⚠ Skipping {to_name} - No email address")
                results["failed"] += 1
                continue

            # Personalize subject
            subject = subject_template.replace("{name}", first_name)

            # Send email
            success = self.send_email_outlook(
                to_email=to_email,
                to_name=to_name,
                subject=subject,
                body=email_template,
                sender_email=sender_email,
                sender_password=sender_password
            )

            if success:
                results["sent"] += 1
            else:
                results["failed"] += 1

            # Be polite - wait between emails
            time.sleep(2)

        print("=" * 60)
        print(f"\n✓ Email campaign complete!")
        print(f"  Sent: {results['sent']}")
        print(f"  Failed: {results['failed']}")

        return results

    def export_to_excel(self, df: pd.DataFrame, filename: str = None) -> None:
        """Export DataFrame to Excel file"""
        if filename is None:
            filename = f"rocketreach_contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"\nData exported to: {filename}")


# Example usage
if __name__ == "__main__":
    # ============================================================================
    # CONFIGURATION
    # ============================================================================

    # RocketReach API Key - LOAD FROM ENVIRONMENT VARIABLE
    API_KEY = os.getenv("ROCKETREACH_API_KEY")
    if not API_KEY:
        print("ERROR: ROCKETREACH_API_KEY environment variable not set!")
        print("Please set it with: export ROCKETREACH_API_KEY='your_key_here'")
        exit(1)

    # Email Configuration (for Outlook/Office 365)
    SENDER_EMAIL = os.getenv("SENDER_EMAIL", "your_email@u.nus.edu")
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "your_password")

    # Initialize extractor (will load contact history to avoid duplicates)
    extractor = RocketReachExtractor(API_KEY)

    # ============================================================================
    # STEP 1: DEFINE SEARCH CRITERIA
    # ============================================================================

    # NOTE: At least one search parameter is required.
    # Uncomment and customize the filters you want to use.
    search_criteria = {
        "query": {
            # Target specific finance sectors
            # "current_title": ["Analyst", "Associate", "Vice President", "Managing Director"],

            # Investment Banking firms
            # "current_employer": ["Goldman Sachs", "Morgan Stanley", "JP Morgan", "Citi"],

            # Consulting firms
            # "current_employer": ["McKinsey", "Bain", "BCG", "Deloitte"],

            # PE/VC firms
            "current_employer": ["Blackstone", "KKR", "Sequoia Capital", "Andreessen Horowitz"],

            # Location filters
            # "location": ["New York", "San Francisco", "Singapore"],

            # Management levels
            # "management_level": ["Manager", "Director", "VP", "C-Level"],

            # Alumni from specific schools
            # "school": ["National University of Singapore", "Stanford University", "Harvard University"]
        }
    }

    # ============================================================================
    # STEP 2: EXTRACT CONTACTS
    # ============================================================================

    print("\n" + "=" * 80)
    print("STEP 1: EXTRACTING CONTACTS FROM ROCKETREACH")
    print("=" * 80)

    # Extract contacts (automatically skips duplicates and classifies sectors)
    contacts_df = extractor.extract_all_contacts(search_criteria, max_results=50)

    if contacts_df.empty:
        print("\n⚠️ No contacts extracted. Exiting...")
        exit()

    # Display sector breakdown
    print("\n📊 Sector Breakdown:")
    print(contacts_df['sector'].value_counts())

    # ============================================================================
    # STEP 3: EXPORT TO EXCEL
    # ============================================================================

    print("\n" + "=" * 80)
    print("STEP 2: EXPORTING TO EXCEL")
    print("=" * 80)

    output_filename = "internship_contacts.xlsx"
    extractor.export_to_excel(contacts_df, output_filename)

    # ============================================================================
    # STEP 4: SEND EMAILS (OPTIONAL)
    # ============================================================================

    # Uncomment the following section to send automated emails

    # print("\n" + "=" * 80)
    # print("STEP 3: SENDING PERSONALIZED EMAILS")
    # print("=" * 80)
    #
    # # Email template with personalization
    # email_template = """
    # Dear {name},
    #
    # I hope this email finds you well. My name is [Your Name], and I am currently
    # a [Your Year] student at the National University of Singapore studying [Your Major].
    #
    # I came across your profile and was impressed by your experience at {company}.
    # I am very interested in learning more about your career path in {sector}.
    #
    # Would you be available for a brief 15-minute informational chat in the coming weeks?
    # I would love to learn from your insights and experiences.
    #
    # Thank you for considering my request. I look forward to hearing from you.
    #
    # Best regards,
    # [Your Name]
    # [Your Email]
    # [Your LinkedIn]
    # """
    #
    # subject_template = "NUS Student Seeking Career Advice"
    #
    # # Send emails (will use email_1 by default)
    # results = extractor.send_bulk_emails(
    #     contacts_df=contacts_df,
    #     email_template=email_template,
    #     subject_template=subject_template,
    #     sender_email=SENDER_EMAIL,
    #     sender_password=SENDER_PASSWORD,
    #     email_column="email_1"  # Use the primary email
    # )

    # ============================================================================
    # SUMMARY
    # ============================================================================

    print("\n" + "=" * 80)
    print("✓ ALL DONE!")
    print("=" * 80)
    print(f"Total contacts extracted: {len(contacts_df)}")
    print(f"Exported to: {output_filename}")
    print(f"Contact history saved to: {extractor.history_file}")

    # Display rate limit usage
    print("\n📊 Rate Limit Usage:")
    status = extractor.get_rate_limit_status()
    print(f"   Lookups:")
    for window, stats in status['lookup'].items():
        print(f"     {window.capitalize():8}: {stats['used']:4}/{stats['limit']:5} ({stats['remaining']:5} remaining)")

    print("\nTip: Run the script again to fetch more contacts. Duplicates will be")
    print("     automatically skipped based on your contact history.")
    print("=" * 80)