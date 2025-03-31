########################################## TEXT PARSING ##########################################
########################################## TEXT PARSING ##########################################
########################################## TEXT PARSING ##########################################

    def create_preset(self, file_list=None, keyword_profiles=None, preset_name="TEXT_", highlight_keywords=True, 
                      output_option="Single output", max_length=200, metadata_settings=True, output_folder=None, 
                      is_gui=True, metadata_prefix=";;"):
        """Create a preset from selected files"""
        self.load_presets()
        
        # Initialize selected_files
        selected_files = file_list if file_list else []

        if is_gui:
            self.load_presets(use_cache=False)
            self.update_selection_cache()
            
            dialog = MultiFolderSelector(self, preset_name)
            self.init_styles(dialog=dialog)

            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                selected_files = dialog.selected_files  # Changed from get_selected_files() to selected_files
                highlight_keywords = dialog.highlight_keywords_checkbox.isChecked()  # Direct access
                output_option = dialog.output_option_dropdown.currentText()  # Direct access
                metadata_settings = dialog.extract_metadata_checkbox.isChecked()  # Direct access
                preset_name = dialog.preset_name_edit.text()  # Direct access
                max_length = int(dialog.max_length_edit.text()) if dialog.max_length_edit.text().isdigit() else 200
                keyword_profiles = dialog.get_all_keyword_profiles()

                if not selected_files:
                    self.show_info_message('No Selection', 'No files were selected.')
                    return
            else:
                return

        # Process files
        all_results = {}
        total_sentences = 0

        print(111111, keyword_profiles)
        print(222222, selected_files)


        start_time = time.time()

        print("MULTITHREADING : OFF")
        file_results = self.process_text_files(
        file_paths=selected_files,
        keyword_profiles=keyword_profiles,
        highlight_keywords=highlight_keywords,
        max_length=max_length,
        metadata_settings=metadata_settings)


        for keyword, sentences in file_results.items():
            if keyword not in all_results:
                all_results[keyword] = []
            all_results[keyword].extend(sentences)



        # Determine the output folder
        target_folder = output_folder if output_folder else self.text_presets_dir
        os.makedirs(target_folder, exist_ok=True)

        # Create the combined output file and count unique sentences
        combined_output_path = os.path.join(target_folder, f"{preset_name}.txt")
        seen_sentences = set()

        with open(combined_output_path, 'w', encoding='utf-8') as output_file:
            for sentences in all_results.values():
                for sentence_data in sentences:
                    sentence_key = (sentence_data[0], sentence_data[1])  # sentence and filepath
                    if sentence_key not in seen_sentences:
                        seen_sentences.add(sentence_key)
                        total_sentences += 1
                        if metadata_settings:
                            sentence, filepath, metadata = sentence_data  # Now includes metadata
                            output_file.write(f'["""{sentence}""","""{metadata}"""]\n\n')
                        else:
                            sentence = sentence_data[0]
                            output_file.write(f'{sentence}\n\n')

        # If "All output" is selected, create individual keyword files
        if output_option == "All output":
            for keyword, sentences in all_results.items():
                if sentences:
                    keyword_output_path = os.path.join(
                        target_folder, f"{preset_name}_{keyword}.txt"
                    )
                    with open(keyword_output_path, 'w', encoding='utf-8') as output_file:
                        for sentence_data in sentences:
                            if metadata_settings:
                                sentence, filepath, metadata = sentence_data
                                output_file.write(f'["""{sentence}""","""{metadata}"""]\n\n')
                            else:
                                sentence = sentence_data[0]
                                output_file.write(f'{sentence}\n\n')

        # End timer and calculate elapsed time
        elapsed_time = time.time() - start_time

        # Show summary message and reload presets if using GUI
        summary_message = (f"Successfully extracted {total_sentences} unique sentences to: {preset_name}.txt in {elapsed_time:.2f} seconds!")
        if is_gui:
            self.show_info_message('Extraction Complete', summary_message)
            self.load_presets()
        print(summary_message)









    def create_keyword_profiles(self, keyword_input):
        """
        Creates keyword profiles based on the user input.
        """
        profiles = []
        for kw in keyword_input:
            if not kw.startswith(';'):  # Ignore comments (those starting with ;)
                profile = self.create_single_keyword_profile(kw)  # Use a method to create a single keyword profile
                profiles.append(profile)
        return profiles

    def create_single_keyword_profile(self, keyword):
        """
        Creates a single keyword profile.
        Modify this method based on how you want each keyword profile to be structured.
        """
        # Example of simple profile creation
        return {'keyword': keyword, 'options': {'highlight': True}}  # Customize as necessary








    def process_text_files(self, file_paths, keyword_profiles, highlight_keywords=True, 
                         max_length=200, metadata_settings=True, metadata_prefix=";;"):
        """
        Process a single text file (EPUB, PDF, or TXT) and return extracted sentences.
        Updated to handle ignored keywords from [0] file and single file processing.
        """
        # Separate ignored keywords (from [0] file) and regular keywords

        # Process ignored keywords
        ignored_keywords = [
            keyword[1:] for profile_keywords in keyword_profiles.values() 
            for keyword in profile_keywords if keyword.startswith('!')
        ]
        for profile_keywords in keyword_profiles.values():
            profile_keywords[:] = [keyword for keyword in profile_keywords if not keyword.startswith('!')]

        # Remove duplicates across all profiles
        seen_keywords = set()
        for profile, keywords in keyword_profiles.items():
            unique_keywords = []
            for keyword in keywords:
                if keyword not in seen_keywords:
                    unique_keywords.append(keyword)
                    seen_keywords.add(keyword)
            keyword_profiles[profile] = unique_keywords

        # Remove duplicates from ignored keywords
        ignored_keywords = list(set(ignored_keywords))

        #print("Keywords by profile (unique)[0:5]:", keyword_profiles)
        #print("Ignored keywords (unique)[0:5]:", ignored_keywords)


        # Initialize storage for combined sentences and processed keywords
        combined_sentences = {
            keyword: [] for keywords in keyword_profiles.values() 
            for keyword in keywords
        }
        processed_keywords = []

        # Process all profiles and extract sentences
        for profile_number, keywords in keyword_profiles.items():
            if keywords:
                self.extract_sentences_with_keywords(
                    file_paths, keywords, combined_sentences, 
                    processed_keywords, max_length, metadata_settings, metadata_prefix
                )

        # Filter out sentences with ignored keywords and store full file paths
        filtered_sentences = {
            keyword: [
                sentence_data for sentence_data in sentences
                if not self.contains_ignored_keyword(sentence_data[0], ignored_keywords)
            ]
            for keyword, sentences in combined_sentences.items()
        }

        # Reset processed keywords for highlighting
        processed_keywords = []

        # Highlight keywords if requested
        if highlight_keywords:
            filtered_sentences = self.process_highlight_keywords(
                filtered_sentences, keyword_profiles, processed_keywords
            )

        return filtered_sentences



    def get_book_metadata(self, file_path, metadata_prefix=";;"):
        """
        Extract metadata from book files.
        Returns metadata string with optional prefix from filename.
        """
        filename = os.path.basename(file_path)
        filename_without_ext = os.path.splitext(filename)[0]
        
        # Extract prefix if present
        prefix = ""
        if metadata_prefix in filename_without_ext:
            prefix, rest = filename_without_ext.split(metadata_prefix, 1)
            filename_without_ext = rest.replace('_', ' ').strip()
        
        # Default values
        title = filename_without_ext
        author = "Unknown Author"
        date = "Unknown Date"
        
        try:
            if file_path.endswith('.epub'):
                book = epub.read_epub(file_path)
                
                # Get title
                if book.get_metadata('DC', 'title'):
                    title = book.get_metadata('DC', 'title')[0][0]
                
                # Get author
                if book.get_metadata('DC', 'creator'):
                    author = book.get_metadata('DC', 'creator')[0][0]
                
                # Get date
                if book.get_metadata('DC', 'date'):
                    date = book.get_metadata('DC', 'date')[0][0]
                    year_match = re.search(r'\d{4}', date)
                    if year_match:
                        date = year_match.group(0)
                
            elif file_path.endswith('.pdf'):
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    if reader.metadata:
                        if reader.metadata.get('/Title'):
                            title = reader.metadata['/Title']
                        if reader.metadata.get('/Author'):
                            author = reader.metadata['/Author']
                        if reader.metadata.get('/CreationDate'):
                            date_str = reader.metadata['/CreationDate']
                            year_match = re.search(r'D:(\d{4})', date_str)
                            if year_match:
                                date = year_match.group(1)
            
            # Clean up metadata
            title = title.strip()
            author = author.strip()
            date = date.strip()
            
            if not title:
                title = filename_without_ext
                
        except Exception as e:
            print(f"Error extracting metadata from {filename}: {str(e)}")
            title = filename_without_ext
        
        # Format the metadata string with prefix
        metadata = prefix.strip()
        if metadata:
            metadata += " - "
        metadata += title
        if author != "Unknown Author":
            metadata += f" by {author}"
        if date != "Unknown Date":
            metadata += f" - {date}"
        
        return metadata


    def get_keyword_forms(self, keyword):
        """
        Get the forms of a keyword, handling the '&' prefix and combined keywords.
        Returns a list of forms and a boolean indicating if it's an exact match.
        """
        if keyword.startswith('&'):
            return [keyword[1:]]  # Single keyword, exact match
        else:
            return [self.get_singular_form(keyword), self.get_plural_form(keyword)]  # Single keyword, both forms


    def contains_ignored_keyword(self, sentence, ignored_keywords):
        for ignored_keyword in ignored_keywords:
            # Handle cases with both forms ignored or only plural ignored
            if ignored_keyword.startswith('!&'):
                # Ignore only the plural form
                base_ignored_keyword = ignored_keyword.lstrip('!&')
                forms_to_ignore = [base_ignored_keyword]  # Only plural form
            else:
                # Ignore both singular and plural forms
                base_ignored_keyword = ignored_keyword.lstrip('!')
                forms_to_ignore = self.get_keyword_forms(base_ignored_keyword)  # Both forms
            # Check if any form is present in the sentence
            for form in forms_to_ignore:
                if re.search(r'\b{}\b'.format(re.escape(form)), sentence, re.IGNORECASE):
                    return True
        return False    




    def process_highlight_keywords(self, filtered_sentences, profiles, processed_keywords):
        """
        Highlight keywords and their forms in sentences with the appropriate number of brackets based on the profile name.
        Updated to handle metadata in sentence data.
        """
        for profile_name, keywords in profiles.items():
            # Extract the numeric part from the profile name (e.g., 'Keywords_1' -> 1)
            match = re.search(r'(\d+)', profile_name)
            bracket_count = int(match.group(1)) if match else 1  # Default to 1 if no number is found

            # Construct the bracket style for this profile
            left_bracket = "{" * bracket_count
            right_bracket = "}" * bracket_count

            # Process each keyword in the profile
            for keyword in keywords:
                # Get all forms of the keyword(s)
                forms_list = self.get_keyword_forms(keyword)
                
                # Flatten the forms list for highlighting
                all_forms = [form for form in forms_list]
                forms_lower = [form.lower() for form in all_forms]
                print(12121212, all_forms)
                if any(form in processed_keywords for form in forms_lower):
                    continue
                
                # Create pattern to match any of the keyword forms
                pattern = re.compile(
                    r'(?<!\w)({})\b'.format("|".join(map(re.escape, all_forms))), 
                    re.IGNORECASE
                )

                # Highlight keywords in all sentences
                for key, sentence_data_list in filtered_sentences.items():
                    for i, sentence_data in enumerate(sentence_data_list):
                        def replace_func(match):
                            # Wrap the matched word in the appropriate brackets
                            original_word = match.group(0)
                            print(777,original_word)
                            return f"{left_bracket}{original_word}{right_bracket}"

                        # Update the sentence with highlighted keywords, preserving the metadata
                        if len(sentence_data) == 3:  # If we have metadata
                            sentence, filepath, metadata = sentence_data
                            highlighted_sentence = pattern.sub(replace_func, sentence)
                            filtered_sentences[key][i] = (highlighted_sentence, filepath, metadata)
                        else:  # If we don't have metadata
                            sentence, filepath = sentence_data
                            highlighted_sentence = pattern.sub(replace_func, sentence)
                            filtered_sentences[key][i] = (highlighted_sentence, filepath)

                # Add all forms to processed_keywords
                for form in all_forms:
                    processed_keywords.append(form.lower())

        return filtered_sentences



    def replace_broken_characters(self, text):
        replacements = {
            "“": '"',
            "’": "'",
            "”": '"',
            "—": "-",  # Correct long dash
            "â€“": "-",  # Misinterpreted en dash
            "â€”": "-",  # Misinterpreted em dash
            " ": "",  # Non-breaking space
            "…": "...",
            "‘": "'",
            "â€œ": '"',  # Misinterpreted opening double quote
            "â€": '"',   # Misinterpreted closing double quote or other symbols
            "â€™": "'",  # Misinterpreted apostrophe
            "–": "-",  # Replace en dash if present
        }

        # Create a pattern that matches any of the keys in replacements (sorted by length to handle multi-character sequences first)
        pattern = re.compile('|'.join(re.escape(key) for key in sorted(replacements.keys(), key=len, reverse=True)))

        # Function to replace all occurrences
        def replace(match):
            return replacements[match.group(0)]

        # Replace all occurrences of broken characters with their correct counterparts
        return pattern.sub(replace, text)





    def get_plural_form(self, keyword):
        if keyword.endswith('s'):
            return keyword 
        else:
            return keyword + 's'  # Add 's' for plural

    def get_singular_form(self, keyword):
        if keyword.endswith('s'):
            return keyword[:-1]  # Remove 's' for singular
        else:
            return keyword

            
       
    def extract_sentences_with_keywords(self, file_paths, keywords, combined_sentences, processed_keywords, max_length, metadata_settings=True, metadata_prefix=";;"):
        """
        Extract sentences containing the provided keywords from the list of files.
        Optimized to process each file only once and pre-filter keywords.
        """
        def match_keywords(forms_list, sentence, max_length=200):
            def find_keyword_in_sentence(forms, sentence):
                for form in forms:
                    if re.search(r'\b{}\b'.format(re.escape(form)), sentence, re.IGNORECASE):
                        return form
                return None

            found_keywords = []
            for forms in forms_list:
                found_keyword = find_keyword_in_sentence(forms, sentence)
                if not found_keyword:
                    return False
                found_keywords.append(found_keyword)

            return truncate_sentence_around_keywords(sentence, found_keywords, max_length)

        def truncate_sentence_around_keywords(sentence, keywords, max_length=200):
            positions = []
            for keyword in keywords:
                match = re.search(r'\b{}\b'.format(re.escape(keyword)), sentence, re.IGNORECASE)
                if match:
                    positions.append((match.start(), match.end()))
            
            if not positions:
                return self.truncate_sentence(sentence, max_length)
            
            positions.sort()
            start_pos = positions[0][0]
            end_pos = positions[-1][1]
            context_length = (max_length - (end_pos - start_pos)) // 2
            
            start = max(0, start_pos - context_length)
            end = min(len(sentence), end_pos + context_length)
            
            if start > 0:
                start = sentence.rfind(' ', 0, start) + 1
            if end < len(sentence):
                end = sentence.rfind(' ', end) + 1
            
            truncated = sentence[start:end].strip()
            if start > 0:
                truncated = '...' + truncated
            if end < len(sentence):
                truncated = truncated + '...'
            
            return truncated

        def extract_text_from_epub(file_path):
            book = epub.read_epub(file_path)
            full_text = ""
            for item in book.get_items_of_type(ITEM_DOCUMENT):
                content = item.get_body_content().decode('utf-8')
                soup = BeautifulSoup(content, 'html.parser')
                full_text += soup.get_text(separator=' ')
            return full_text

        def clean_linebreaks(text):
            return re.sub(r'(\n\s*)+', ' ', text).strip()

        # Pre-process keywords and their forms
        keyword_forms_map = {}
        for keyword in keywords:
            forms_list = self.get_keyword_forms(keyword)
            # Skip if all forms have been processed
            all_forms = [form.lower() for sublist in forms_list for form in sublist]
            if all(form in processed_keywords for form in all_forms):
                continue
            keyword_forms_map[keyword] = (forms_list, all_forms)

        unique_sentences = set()

        # Process each file once
        for file_path in file_paths:
            print(555555555555, file_path)
            filename = os.path.basename(file_path)
            
            # Extract metadata once per file if needed
            metadata = None
            if metadata_settings:
                try:
                    metadata = self.get_book_metadata(file_path, metadata_prefix)
                except Exception as e:
                    print(f"Error extracting metadata from {filename}: {str(e)}")
                    metadata = filename
            
            # Read file content
            try:
                if file_path.endswith('.pdf'):
                    with open(file_path, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        full_text = "".join([page.extract_text() or "" for page in reader.pages])
                elif file_path.endswith('.txt'):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            full_text = file.read()
                    except UnicodeDecodeError:
                        with open(file_path, 'r', encoding='iso-8859-1') as file:
                            full_text = file.read()
                elif file_path.endswith('.epub'):
                    full_text = extract_text_from_epub(file_path)
                else:
                    print(f"Unsupported file type: {file_path}")
                    continue

                # Clean and split text into sentences
                full_text = clean_linebreaks(full_text)
                print(666666666666, full_text[0:100])
                # Pre-filter keywords based on simple text matching
                active_keywords = {}
                for keyword, (forms_list, all_forms) in keyword_forms_map.items():
                    # Check if any form of the keyword appears in the text
                    if any(form.lower() in full_text.lower() for forms in forms_list for form in forms):
                        active_keywords[keyword] = (forms_list)

                if not active_keywords:
                    continue  # Skip processing if no keywords found in file

                # Process sentences only if we have matching keywords
                sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', full_text)
                
                for sentence in sentences:
                    sentence_cleaned = self.replace_broken_characters(sentence.strip())
                    
                    # Check each active keyword
                    for keyword, (forms_list) in active_keywords.items():
                        matched_sentence_trimmed = match_keywords(forms_list, sentence_cleaned, max_length)
                        if matched_sentence_trimmed:
                            if metadata_settings:
                                sentence_data = (matched_sentence_trimmed, file_path, metadata)
                            else:
                                sentence_data = (matched_sentence_trimmed, file_path)
                                
                            if sentence_data not in unique_sentences:
                                unique_sentences.add(sentence_data)
                                if keyword not in combined_sentences:
                                    combined_sentences[keyword] = []
                                combined_sentences[keyword].append(sentence_data)

                        #print(77777777, combined_sentences)

            except Exception as e:
                print(f"Error processing file {file_path}: {str(e)}")
                continue

        # Update processed keywords
        for _, (_,  all_forms) in keyword_forms_map.items():
            processed_keywords.extend(all_forms)

        print(f"Processed keywords: {processed_keywords[0:5]} ...")
        print(f"Extracted {len(unique_sentences)} unique sentences.")

                                
########################################## TEXT PARSING END ##########################################
########################################## TEXT PARSING END ##########################################
########################################## TEXT PARSING END ##########################################