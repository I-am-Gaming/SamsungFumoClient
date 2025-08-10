import requests
import xml.etree.ElementTree as ET
import json
import string
import os
import hashlib

# Ranges
bl = list(string.digits) + list(string.ascii_uppercase)  # Bootloader 0-9 + A-Z
yr = ["Y", "Z"]  # Year letters
ul = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "Z"]  # OS update letters (+ Z)
br = list(string.digits[1:]) + list(string.ascii_uppercase)  # Build revision 1-9 + A-Z
mon = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]  # Months
up = ["U", "S"]  # Update Type

def get_firmware(model, csc):
    base_url = f"https://fota-cloud-dn.ospserver.net/firmware/{csc}/{model}"
    version_url = f"{base_url}/version.xml"
    test_url = f"{base_url}/version.test.xml"

    try:
        resp = requests.get(version_url, timeout=5)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        latest = root.find(".//latest")

        if latest is None or not latest.text:
            return None, [], [], []

        fw_string = latest.text.strip()
        parts = fw_string.split("/")
        ap, csc_code, *bp_part = parts
        bp = bp_part[0] if bp_part else None

        fixed_ap = ap[:-6]
        fixed_csc = csc_code[:-5]
        fixed_bp = bp[:-6] if bp else None

        # Generate AP candidates
        ap_candidates = []
        for update_type_new in up:
            for bl_new in bl:
                for ul_new in ul:
                    for year in yr:
                        for month in mon:
                            for rev in br:
                                ap_candidates.append(
                                    fixed_ap + update_type_new + bl_new + ul_new + year + month + rev
                                )

        # Generate CSC candidates
        csc_candidates = []
        for bl_new in bl:
            for ul_new in ul:
                for year in yr:
                    for month in mon:
                        for rev in br:
                            csc_candidates.append(
                                fixed_csc + bl_new + ul_new + year + month + rev
                            )

        # Generate BP candidates (same structure as AP)
        bp_candidates = []
        if fixed_bp:
            for update_type_new in up:
                for bl_new in bl:
                    for ul_new in ul:
                        for year in yr:
                            for month in mon:
                                for rev in br:
                                    bp_candidates.append(
                                        fixed_bp + update_type_new + bl_new + ul_new + year + month + rev
                                    )

        # Fetch hashes
        resp_test = requests.get(test_url, timeout=5)
        resp_test.raise_for_status()
        root_test = ET.fromstring(resp_test.text)
        hashes = [val.text.strip() for val in root_test.findall(".//value")]

        return (ap, csc_code, bp), hashes, ap_candidates, csc_candidates, bp_candidates

    except Exception as e:
        print(f"❌ Error fetching {model} ({csc}): {e}")
        return None, [], [], [], []


def load_existing_devices():
    """Load already processed devices to detect first-time devices"""
    existing_devices = set()
    
    try:
        if os.path.exists("firmware_data.json"):
            with open("firmware_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                existing_devices.update(data.keys())
    except Exception as e:
        print(f"⚠️ Warning: Could not load existing devices: {e}")
    
    return existing_devices

def load_existing_hashes():
    """Load already decrypted firmware hashes to avoid duplicates"""
    existing_hashes = set()
    
    try:
        # Load from firmware_matches.json if it exists
        if os.path.exists("firmware_matches.json"):
            with open("firmware_matches.json", "r", encoding="utf-8") as f:
                content = f.read()
                # Extract hash keys from existing JSON
                import re
                hash_pattern = r'"([a-f0-9]{32})":'
                existing_hashes.update(re.findall(hash_pattern, content))
    except Exception as e:
        print(f"⚠️ Warning: Could not load existing hashes: {e}")
    
    return existing_hashes

def main():
    import datetime
    devices_file = "devices.txt"
    output_file = "firmware_data.json"

    all_data = {}

    existing_hashes = load_existing_hashes()
    existing_devices = load_existing_devices()
    print(f"📋 Loaded {len(existing_hashes)} existing decrypted firmware hashes")
    print(f"📋 Loaded {len(existing_devices)} existing devices")

    os.makedirs("output_candidates", exist_ok=True)

    with open(devices_file, "r") as f:
        devices = [line.strip() for line in f if line.strip()]

    for line in devices:
        parts = line.split(",")
        if len(parts) != 3:
            print(f"⚠️ Invalid line format in devices.txt: {line}")
            continue

        device_name, model, csc_list = parts
        cscs = csc_list.split("|")

        for csc in cscs:
            csc = csc.strip()
            try:
                print(f"\n🔄 Processing {device_name} ({model}) with CSC: {csc}")
                fixed_values, hashes, ap_candidates, csc_candidates, bp_candidates = get_firmware(model, csc)

                if not fixed_values:
                    print(f"⚠️ No firmware found for {device_name} {model} ({csc})")
                    continue

                org_ap, org_csc, org_bp = fixed_values
                all_matches = []
                new_matches = []

                # Create the official firmware string for comparison
                official_firmware = f"{org_ap}/{org_csc}/{org_bp}" if org_bp else f"{org_ap}/{org_csc}"

                # --- gen_ap / org_csc / org_bp ---
                saved_apgen = []
                for ap_new in ap_candidates:
                    ap_bl = ap_new[len(org_ap[:-6]) + 1]
                    ap_ul = ap_new[len(org_ap[:-6]) + 2]
                    csc_bl = org_csc[len(org_csc[:-5])]
                    csc_ul = org_csc[len(org_csc[:-5]) + 1]
                    if org_bp:
                        bp_bl = org_bp[len(org_bp[:-6]) + 1]
                        bp_ul = org_bp[len(org_bp[:-6]) + 2]
                        if ap_bl == csc_bl == bp_bl and ap_ul == csc_ul == bp_ul:
                            saved_apgen.append(f"{ap_new}/{org_csc}/{org_bp}")
                    else:
                        if ap_bl == csc_bl and ap_ul == csc_ul:
                            saved_apgen.append(f"{ap_new}/{org_csc}")

                # --- org_ap / gen_csc / org_bp ---
                saved_cscgen = []
                for csc_new in csc_candidates:
                    ap_bl = org_ap[len(org_ap[:-6]) + 1]
                    ap_ul = org_ap[len(org_ap[:-6]) + 2]
                    csc_bl = csc_new[len(org_csc[:-5])]
                    csc_ul = csc_new[len(org_csc[:-5]) + 1]
                    if org_bp:
                        bp_bl = org_bp[len(org_bp[:-6]) + 1]
                        bp_ul = org_bp[len(org_bp[:-6]) + 2]
                        if ap_bl == csc_bl == bp_bl and ap_ul == csc_ul == bp_ul:
                            saved_cscgen.append(f"{org_ap}/{csc_new}/{org_bp}")
                    else:
                        if ap_bl == csc_bl and ap_ul == csc_ul:
                            saved_cscgen.append(f"{org_ap}/{csc_new}")

                # --- org_ap / org_csc / gen_bp ---
                saved_bpgen = []
                if org_bp:
                    for bp_new in bp_candidates:
                        ap_bl = org_ap[len(org_ap[:-6]) + 1]
                        ap_ul = org_ap[len(org_ap[:-6]) + 2]
                        csc_bl = org_csc[len(org_csc[:-5])]
                        csc_ul = org_csc[len(org_csc[:-5]) + 1]
                        bp_bl = bp_new[len(org_bp[:-6]) + 1]
                        bp_ul = bp_new[len(org_bp[:-6]) + 2]
                        if ap_bl == csc_bl == bp_bl and ap_ul == csc_ul == bp_ul:
                            saved_bpgen.append(f"{org_ap}/{org_csc}/{bp_new}")

                # --- gen_ap(Z) / gen_csc(Z) / gen_bp(normal) ---
                saved_zset = []
                if org_bp:
                    fixed_ap = org_ap[:-6]
                    fixed_csc = org_csc[:-5]
                    fixed_bp = org_bp[:-6]
                    for update_type_new in up:
                        for bl_new in bl:
                            for year in yr:
                                for month in mon:
                                    for rev in br:
                                        for bp_ul in [u for u in ul if u != "Z"]:
                                            ap_new = f"{fixed_ap}U{bl_new}Z{year}{month}{rev}"
                                            csc_new = f"{fixed_csc}{bl_new}Z{year}{month}{rev}"
                                            bp_new = f"{fixed_bp}U{bl_new}{bp_ul}{year}{month}{rev}"
                                            saved_zset.append(f"{ap_new}/{csc_new}/{bp_new}")

                # --- gen_ap / gen_csc / gen_bp (current_bl to current_bl+2 and update_letter to update_letter+2) ---
                saved_genall = []
                fixed_ap = org_ap[:-6]
                fixed_csc = org_csc[:-5]
                fixed_bp = org_bp[:-6] if org_bp else None
                
                # Get current BL and update letter from original firmware
                current_bl = org_ap[len(fixed_ap) + 1]
                current_ul = org_ap[len(fixed_ap) + 2]
                
                # Find indices for current values
                current_bl_idx = bl.index(current_bl) if current_bl in bl else 0
                current_ul_idx = ul.index(current_ul) if current_ul in ul else 0
                
                # Generate candidates with current_bl to current_bl+2 and update_letter to update_letter+2
                for update_type_new in up:
                    for bl_offset in range(3):
                        bl_idx = (current_bl_idx + bl_offset) % len(bl)
                        bl_new = bl[bl_idx]
                        
                        for ul_offset in range(3):
                            ul_idx = (current_ul_idx + ul_offset) % len(ul)
                            ul_new = ul[ul_idx]
                            
                            for year in yr:
                                for month in mon:
                                    for rev in br:
                                        ap_new = f"{fixed_ap}{update_type_new}{bl_new}{ul_new}{year}{month}{rev}"
                                        csc_new = f"{fixed_csc}{bl_new}{ul_new}{year}{month}{rev}"
                                        
                                        if org_bp:
                                            bp_new = f"{fixed_bp}{update_type_new}{bl_new}{ul_new}{year}{month}{rev}"
                                            ap_bl = ap_new[len(fixed_ap) + 1]
                                            ap_ul = ap_new[len(fixed_ap) + 2]
                                            csc_bl = csc_new[len(fixed_csc)]
                                            csc_ul = csc_new[len(fixed_csc) + 1]
                                            bp_bl = bp_new[len(fixed_bp) + 1]
                                            bp_ul = bp_new[len(fixed_bp) + 2]
                                            
                                            if ap_bl == csc_bl == bp_bl and ap_ul == csc_ul == bp_ul:
                                                saved_genall.append(f"{ap_new}/{csc_new}/{bp_new}")
                                        else:
                                            ap_bl = ap_new[len(fixed_ap) + 1]
                                            ap_ul = ap_new[len(fixed_ap) + 2]
                                            csc_bl = csc_new[len(fixed_csc)]
                                            csc_ul = csc_new[len(fixed_csc) + 1]
                                            
                                            if ap_bl == csc_bl and ap_ul == csc_ul:
                                                saved_genall.append(f"{ap_new}/{ap_new}")

                # --- gen_ap / gen_csc (no BP) for devices without BP ---
                saved_genap_csc = []
                if not org_bp:
                    for ap_new in ap_candidates:
                        saved_genap_csc.append(f"{ap_new}/{ap_new}")

                # Beta-builds
                saved_beta_aseries = []
                if org_bp:
                    fixed_ap = org_ap[:-6]
                    fixed_csc = org_csc[:-5]
                    fixed_bp = org_bp[:-6]
                    if fixed_ap[0:1] == "A":
                        update_letter = "Z"
                        update_type = "U"
                        
                        for bl_new in bl:
                            for year_letter in yr:
                                for month_letter in mon:
                                    for build_no in br:
                                        ap_val = f"{fixed_ap}{update_type}{bl_new}{update_letter}{year_letter}{month_letter}{build_no}"
                                        csc_val = f"{fixed_csc}{bl_new}{update_letter}{year_letter}{month_letter}{build_no}"
                                        bp_val = f"{fixed_bp}{update_type}{bl_new}{update_letter}{year_letter}{month_letter}{build_no}"
                                        saved_beta_aseries.append(f"{ap_val}/{csc_val}/{bp_val}")

                # Check all matches and track new ones
                ap_matches = []
                for combo in saved_apgen:
                    combo_md5 = hashlib.md5(combo.encode()).hexdigest()
                    if combo_md5 in hashes and combo != official_firmware:
                        ap_matches.append(combo)
                        match_entry = f"**AP Match:** {combo}"
                        all_matches.append(match_entry)
                        if combo_md5 not in existing_hashes:
                            new_matches.append(match_entry)

                csc_matches = []
                for combo in saved_cscgen:
                    combo_md5 = hashlib.md5(combo.encode()).hexdigest()
                    if combo_md5 in hashes and combo != official_firmware:
                        csc_matches.append(combo)
                        match_entry = f"**CSC Match:** {combo}"
                        all_matches.append(match_entry)
                        if combo_md5 not in existing_hashes:
                            new_matches.append(match_entry)

                bp_matches = []
                if saved_bpgen:
                    for combo in saved_bpgen:
                        combo_md5 = hashlib.md5(combo.encode()).hexdigest()
                        if combo_md5 in hashes and combo != official_firmware:
                            bp_matches.append(combo)
                            match_entry = f"**BP Match:** {combo}"
                            all_matches.append(match_entry)
                            if combo_md5 not in existing_hashes:
                                new_matches.append(match_entry)

                zset_matches = []
                if saved_zset:
                    for combo in saved_zset:
                        combo_md5 = hashlib.md5(combo.encode()).hexdigest()
                        if combo_md5 in hashes and combo != official_firmware:
                            zset_matches.append(combo)
                            match_entry = f"**Zset Match:** {combo}"
                            all_matches.append(match_entry)
                            if combo_md5 not in existing_hashes:
                                new_matches.append(match_entry)

                genap_csc_matches = []
                if saved_genap_csc:
                    for combo in saved_genap_csc:
                        combo_md5 = hashlib.md5(combo.encode()).hexdigest()
                        if combo_md5 in hashes and combo != official_firmware:
                            genap_csc_matches.append(combo)
                            match_entry = f"**GenAP-CSC Match:** {combo}"
                            all_matches.append(match_entry)
                            if combo_md5 not in existing_hashes:
                                new_matches.append(match_entry)

                genall_matches = []
                if saved_genall:
                    for combo in saved_genall:
                        combo_md5 = hashlib.md5(combo.encode()).hexdigest()
                        if combo_md5 in hashes and combo != official_firmware:
                            genall_matches.append(combo)
                            match_entry = f"**GenAll Match:** {combo}"
                            all_matches.append(match_entry)
                            if combo_md5 not in existing_hashes:
                                new_matches.append(match_entry)

                beta_matches = []
                if saved_beta_aseries:
                    for combo in saved_beta_aseries:
                        combo_md5 = hashlib.md5(combo.encode()).hexdigest()
                        if combo_md5 in hashes and combo != official_firmware:
                            beta_matches.append(combo)
                            match_entry = f"**Beta Match:** {combo}"
                            all_matches.append(match_entry)
                            if combo_md5 not in existing_hashes:
                                new_matches.append(match_entry)

                # Save to text files
                with open(f"output_candidates/{model}_{csc}_AP.txt", "w") as f_ap:
                    f_ap.write("\n".join(ap_matches))
                print(f"✅ Saved AP-gen combos ({len(saved_apgen)} generated, {len(ap_matches)} matches)")

                with open(f"output_candidates/{model}_{csc}_CSC.txt", "w") as f_csc:
                    f_csc.write("\n".join(csc_matches))
                print(f"✅ Saved CSC-gen combos ({len(saved_cscgen)} generated, {len(csc_matches)} matches)")

                if saved_bpgen:
                    with open(f"output_candidates/{model}_{csc}_BP.txt", "w") as f_bp:
                        f_bp.write("\n".join(bp_matches))
                    print(f"✅ Saved BP-gen combos ({len(saved_bpgen)} generated, {len(bp_matches)} matches)")

                if saved_zset:
                    with open(f"output_candidates/{model}_{csc}_Zset.txt", "w") as f_z:
                        f_z.write("\n".join(zset_matches))
                    print(f"✅ Saved AP/CSC-Z & BP-normal combos ({len(saved_zset)} generated, {len(zset_matches)} matches)")

                if saved_genap_csc:
                    with open(f"output_candidates/{model}_{csc}_GenAP_CSC.txt", "w") as f_genap_csc:
                        f_genap_csc.write("\n".join(genap_csc_matches))
                    print(f"✅ Saved GenAP-CSC combos ({len(saved_genap_csc)} generated, {len(genap_csc_matches)} matches)")

                if saved_genall:
                    with open(f"output_candidates/{model}_{csc}_GenAll.txt", "w") as f_genall:
                        f_genall.write("\n".join(genall_matches))
                    print(f"✅ Saved Gen-All combos ({len(saved_genall)} generated, {len(genall_matches)} matches)")

                if saved_beta_aseries:
                    with open(f"output_candidates/{model}_{csc}_Beta.txt", "w") as f_beta:
                        f_beta.write("\n".join(beta_matches))
                    print(f"✅ Saved Beta A-series combos ({len(saved_beta_aseries)} generated, {len(beta_matches)} matches)")

                # Save all matches to different output formats (only new ones)
                if new_matches:
                    print(f"🔍 Debug: Found {len(all_matches)} total matches, {len(new_matches)} are new")
                    
                    # Check if this is a first-time device
                    device_key = f"{model}_{csc}"
                    is_first_time = device_key not in existing_devices
                    
                    # Get proper device name and region
                    def get_device_info(device_name, model, csc):
                        region_names = {
                            'INS': 'Indian', 'KOO': 'Korean', 'BOX': 'European',
                            'EUX': 'European', 'DBT': 'German', 'BTU': 'UK',
                            'XEF': 'French', 'TGY': 'Hong Kong', 'PKD': 'Pakistani'
                        }
                        region_name = region_names.get(csc, csc)
                        return f"{device_name} {region_name} Version"
                    
                    device_info = get_device_info(device_name, model, csc)
                    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    # JSON format - always save
                    json_data = {}
                    firmware_list = []
                    
                    # Process each NEW match
                    for match_line in new_matches:
                        if ": " in match_line:
                            firmware = match_line.split(": ")[1]
                        else:
                            firmware = match_line.replace("**GenAll Match:** ", "").replace("**AP Match:** ", "").replace("**CSC Match:** ", "").replace("**BP Match:** ", "").replace("**Zset Match:** ", "").replace("**GenAP-CSC Match:** ", "").replace("**Beta Match:** ", "")
                        
                        firmware_md5 = hashlib.md5(firmware.encode()).hexdigest()
                        json_data[firmware_md5] = firmware
                        firmware_list.append((firmware, firmware_md5))
                    
                    # Find latest firmware (highest hash value)
                    if firmware_list:
                        latest_firmware = max(firmware_list, key=lambda x: x[1])  # Sort by hash
                        latest_fw, latest_hash = latest_firmware
                    
                    # Write to decrypted_builds.txt - ONLY for existing devices
                    if not is_first_time:
                        with open("decrypted_builds.txt", "a", encoding="utf-8") as f_decrypt_txt:
                            f_decrypt_txt.write(f"*****Record Time:{current_time}*****\n")
                            for firmware, firmware_md5 in firmware_list:
                                f_decrypt_txt.write(f"{device_info.split(' Version')[0]} newly added test firmware version:{firmware}，MD5 value：{firmware_md5}\n")
                        print(f"📝 Added to decrypted_builds.txt (existing device)")
                    else:
                        print(f"🆕 Skipped decrypted_builds.txt (first-time device)")
                    
                    # Write to firmware_list.md - show latest test firmware only
                    with open("firmware_list.md", "a", encoding="utf-8") as f_firmware_md:
                        f_firmware_md.write(f"#### {device_info}: \n")
                        f_firmware_md.write(f"Official Firmware:{official_firmware} \n")
                        if firmware_list:
                            f_firmware_md.write(f"Test Firmware:{latest_fw} \n")
                    
                    # Write to firmware_matches.json - always save all
                    with open("firmware_matches.json", "a", encoding="utf-8") as f_json:
                        for hash_val, firmware in json_data.items():
                            f_json.write(f'    "{hash_val}": "{firmware}",\n')
                    
                    if is_first_time:
                        print(f"🆕 Added {len(new_matches)} NEW matches (first-time device)")
                    else:
                        print(f"🆕 Added {len(new_matches)} NEW matches to all output formats")
                elif len(all_matches) > 0:
                    print(f"ℹ️ Found {len(all_matches)} matches, but all were already decrypted")

                all_data[f"{model}_{csc}"] = {
                    "Device_Name": device_name,
                    "Original_AP": org_ap,
                    "Original_CSC": org_csc,
                    "Original_BP": org_bp,
                    "Hashes": hashes,
                    "AP_gen_count": len(saved_apgen),
                    "CSC_gen_count": len(saved_cscgen),
                    "BP_gen_count": len(saved_bpgen),
                    "Zset_count": len(saved_zset),
                    "GenAll_count": len(saved_genall),
                    "GenAP_CSC_count": len(saved_genap_csc),
                    "Beta_count": len(saved_beta_aseries),
                    "AP_matches": len(ap_matches),
                    "CSC_matches": len(csc_matches),
                    "BP_matches": len(bp_matches),
                    "Zset_matches": len(zset_matches),
                    "GenAll_matches": len(genall_matches),
                    "GenAP_CSC_matches": len(genap_csc_matches),
                    "Beta_matches": len(beta_matches)
                }

            except Exception as e:
                print(f"❌ Error processing {model} ({csc}): {e}")

    with open(output_file, "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"\n✅ All firmware summary saved to {output_file}")

if __name__ == "__main__":
    main()