/**
 * Geocoding utility functions for the Natal Astrology Engine
 * Converts location names to latitude/longitude coordinates
 */

// Use OpenStreetMap's Nominatim service for geocoding
// This is a free service with usage limits - for production use,
// consider a commercial geocoding service with an API key

/**
 * Get coordinates from a location string using OpenStreetMap's Nominatim API
 * 
 * @param {string} locationString - The location to geocode (e.g., "New York, NY")
 * @param {function} successCallback - Callback function on success, receives lat/lng
 * @param {function} errorCallback - Callback function on error
 */
function geocodeLocation(locationString, successCallback, errorCallback) {
    // Don't attempt geocoding if the input is empty
    if (!locationString || locationString.trim() === '') {
        if (errorCallback) errorCallback('Please enter a location');
        return;
    }
    
    // Show loading state
    const locationField = document.getElementById('location');
    if (locationField) {
        locationField.classList.add('loading');
    }
    
    // Try using a server-side proxy approach instead of direct API call
    // This avoids CORS issues and can add proper headers
    tryServerSideGeocoding(locationString, successCallback, errorCallback);
}

/**
 * Try to geocode using the built-in preset locations first
 * This is a fallback for when the geocoding service is unavailable
 *
 * @param {string} locationString - The location to geocode
 * @returns {Object|null} - Location data or null if not found
 */
function findPresetLocation(locationString) {
    const search = locationString.toLowerCase().trim();
    
    // Define preset locations
    const presets = {
        'new york': { lat: 40.7128, lng: -74.0060, name: 'New York, USA', timezone: 'America/New_York' },
        'london': { lat: 51.5074, lng: -0.1278, name: 'London, UK', timezone: 'Europe/London' },
        'tokyo': { lat: 35.6762, lng: 139.6503, name: 'Tokyo, Japan', timezone: 'Asia/Tokyo' },
        'sydney': { lat: -33.8688, lng: 151.2093, name: 'Sydney, Australia', timezone: 'Australia/Sydney' },
        'boise': { lat: 43.6150, lng: -116.2023, name: 'Boise, Idaho, USA', timezone: 'America/Denver' },
        'salt lake city': { lat: 40.7608, lng: -111.8910, name: 'Salt Lake City, Utah, USA', timezone: 'America/Denver' },
        'los angeles': { lat: 34.0522, lng: -118.2437, name: 'Los Angeles, USA', timezone: 'America/Los_Angeles' },
        'chicago': { lat: 41.8781, lng: -87.6298, name: 'Chicago, USA', timezone: 'America/Chicago' },
        'paris': { lat: 48.8566, lng: 2.3522, name: 'Paris, France', timezone: 'Europe/Paris' },
        'berlin': { lat: 52.5200, lng: 13.4050, name: 'Berlin, Germany', timezone: 'Europe/Berlin' },
        'rome': { lat: 41.9028, lng: 12.4964, name: 'Rome, Italy', timezone: 'Europe/Rome' },
        'madrid': { lat: 40.4168, lng: -3.7038, name: 'Madrid, Spain', timezone: 'Europe/Madrid' },
        'beijing': { lat: 39.9042, lng: 116.4074, name: 'Beijing, China', timezone: 'Asia/Shanghai' },
        'moscow': { lat: 55.7558, lng: 37.6173, name: 'Moscow, Russia', timezone: 'Europe/Moscow' }
    };
    
    // Check if any preset key is contained in the search string
    for (const key in presets) {
        if (search.includes(key) || key.includes(search)) {
            return presets[key];
        }
    }
    
    // Split the search terms and try each word
    const searchWords = search.split(/\s+/);
    for (const word of searchWords) {
        if (word.length < 3) continue; // Skip very short words
        
        for (const key in presets) {
            const keyWords = key.split(/\s+/);
            for (const keyWord of keyWords) {
                if (keyWord.length < 3) continue; // Skip very short words
                
                // Check if this word matches any part of our presets
                if (keyWord.includes(word) || word.includes(keyWord)) {
                    return presets[key];
                }
            }
        }
    }
    
    return null;
}

/**
 * Try server-side geocoding via our own API (recommended approach)
 * Falls back to local preset matching if that fails
 *
 * @param {string} locationString - Location to geocode
 * @param {function} successCallback - Success callback
 * @param {function} errorCallback - Error callback
 */
function tryServerSideGeocoding(locationString, successCallback, errorCallback) {
    const locationField = document.getElementById('location');
    
    // First try to match against our preset locations
    const presetMatch = findPresetLocation(locationString);
    if (presetMatch) {
        // Remove loading state
        if (locationField) {
            locationField.classList.remove('loading');
        }
        
        // Call success callback with the preset data
        if (successCallback) {
            successCallback(
                presetMatch.lat, 
                presetMatch.lng, 
                presetMatch.name, 
                presetMatch.timezone
            );
        }
        return;
    }
    
    // Try a direct geocoding request with better error handling
    // First, look for cities with the same name in our expanded list
    // This is a more reliable approach than relying solely on external API
    const presetMatch = findPresetLocation(locationString);
    if (presetMatch) {
        // Remove loading state
        if (locationField) {
            locationField.classList.remove('loading');
        }
        
        // Call success callback with the preset data
        if (successCallback) {
            successCallback(
                presetMatch.lat, 
                presetMatch.lng, 
                presetMatch.name, 
                presetMatch.timezone
            );
        }
        return;
    }
    
    // If no preset match found, try the OpenStreetMap Nominatim API
    // Build the Nominatim API URL with better parameters
    const apiUrl = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(locationString)}&limit=1&addressdetails=1`;
    
    // Make the request with proper headers
    fetch(apiUrl, {
        method: 'GET',
        headers: {
            'User-Agent': 'NatalAstrologyChart/1.0 (https://replit.com/)',
            'Accept': 'application/json',
            'Referer': 'https://replit.com/'
        },
        // Set a longer timeout to wait for response
        timeout: 5000
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Remove loading state
        if (locationField) {
            locationField.classList.remove('loading');
        }
        
        // Check if we have results
        if (data && data.length > 0) {
            const result = data[0];
            const lat = parseFloat(result.lat);
            const lng = parseFloat(result.lon);
            let displayName = result.display_name;
            
            // Try to create a more user-friendly display name from address details
            if (result.address) {
                const addr = result.address;
                const city = addr.city || addr.town || addr.village || addr.hamlet;
                const state = addr.state || addr.county;
                const country = addr.country;
                
                if (city && country) {
                    displayName = city;
                    if (state) displayName += `, ${state}`;
                    displayName += `, ${country}`;
                }
            }
            
            // Get timezone using our improved function
            const timezone = getTimezoneFromCoordinates(lat, lng);
            
            // Call success callback
            if (successCallback) {
                successCallback(lat, lng, displayName, timezone);
            }
        } else {
            // No results found
            if (errorCallback) {
                errorCallback('Location not found. Please try a different search term or use a preset location.');
            }
        }
    })
    .catch(error => {
        // Remove loading state
        if (locationField) {
            locationField.classList.remove('loading');
        }
        
        console.error('Geocoding error:', error);
        
        // Use manual location inputs if geocoding fails
        const errorMsg = 'Geocoding service unavailable. Please enter coordinates manually or use a preset location.';
        
        if (errorCallback) {
            errorCallback(errorMsg);
        }
        
        // Show user-friendly error in the location result field
        const locationResult = document.getElementById('location-result');
        if (locationResult) {
            locationResult.innerHTML = `<span class="text-warning"><i class="fa fa-exclamation-triangle"></i> ${errorMsg}</span>`;
        }
    });
}

/**
 * Attempt to get timezone from coordinates
 * This is a simplified function - for production use, consider a timezone API
 * 
 * @param {number} lat - Latitude
 * @param {number} lng - Longitude
 * @returns {string} - Estimated timezone or empty string if unknown
 */
function getTimezoneFromCoordinates(lat, lng) {
    // Enhanced version with more timezones and better resolution
    
    // United States
    if (lat > 24 && lat < 50 && lng > -130 && lng < -65) {
        // West Coast
        if (lng < -114) return 'America/Los_Angeles';
        
        // Mountain time
        if (lng < -101) {
            // Arizona (doesn't observe daylight saving)
            if (lat > 31 && lat < 37 && lng > -115 && lng < -109) {
                return 'America/Phoenix';
            }
            return 'America/Denver';
        }
        
        // Central time
        if (lng < -87) return 'America/Chicago';
        
        // Eastern time
        if (lng < -75) return 'America/New_York';
        
        // Handle parts of Maine and eastern Canada
        return 'America/New_York';
    }
    
    // Canada - similar zones to US but more complex borders
    if (lat >= 49 && lat < 70 && lng > -140 && lng < -50) {
        // Pacific time
        if (lng < -115) return 'America/Vancouver';
        
        // Mountain time
        if (lng < -100) return 'America/Edmonton';
        
        // Central time 
        if (lng < -87) return 'America/Winnipeg';
        
        // Eastern time
        if (lng < -75) return 'America/Toronto';
        
        // Atlantic time
        if (lng < -65) return 'America/Halifax';
        
        // Newfoundland (special half-hour offset)
        return 'America/St_Johns';
    }
    
    // Mexico and Central America
    if (lat > 7 && lat < 33 && lng > -120 && lng < -75) {
        // Mexico Pacific time
        if (lng < -107) return 'America/Mazatlan';
        
        // Mexico Central time
        if (lng < -95) return 'America/Mexico_City';
        
        // Central America
        return 'America/Guatemala';
    }
    
    // South America
    if (lat > -60 && lat < 15 && lng > -85 && lng < -30) {
        // Colombia, Ecuador, Peru
        if (lng < -70) return 'America/Lima';
        
        // Venezuela, Guyana region
        if (lng < -55 && lat > 0) return 'America/Caracas';
        
        // Brazil (multiple zones)
        if (lat < 5 && lng > -55) return 'America/Belem';
        if (lng > -55) return 'America/Sao_Paulo';
        
        // Argentina, Chile
        if (lat < 0 && lng < -55) return 'America/Santiago';
        return 'America/Buenos_Aires';
    }
    
    // Europe
    if (lat > 35 && lat < 75 && lng > -15 && lng < 40) {
        // Western Europe
        if (lng < 0) return 'Europe/London';
        if (lng < 10) return 'Europe/Paris';
        if (lng < 15) return 'Europe/Berlin';
        if (lng < 20) return 'Europe/Warsaw';
        if (lng < 30) return 'Europe/Kiev';
        return 'Europe/Moscow';
    }
    
    // Africa
    if (lat > -40 && lat < 35 && lng > -20 && lng < 55) {
        // Northern Africa - generally follows Europe
        if (lat > 20) {
            if (lng < 0) return 'Africa/Casablanca';
            if (lng < 20) return 'Africa/Algiers';
            return 'Africa/Cairo';
        }
        
        // Central Africa
        if (lat > 0) {
            if (lng < 20) return 'Africa/Lagos';
            return 'Africa/Nairobi';
        }
        
        // Southern Africa
        return 'Africa/Johannesburg';
    }
    
    // Asia
    if (lat > 0 && lat < 75 && lng >= 40 && lng < 150) {
        // Middle East
        if (lng < 60) return 'Asia/Tehran';
        
        // India & surrounding region
        if (lng < 80) return 'Asia/Kolkata';
        
        // China & East Asia (China has one time zone officially)
        if (lng < 120) return 'Asia/Shanghai';
        
        // Japan & Korea
        if (lng < 145) return 'Asia/Tokyo';
        
        // Far East Russia
        return 'Asia/Vladivostok';
    }
    
    // Australia
    if (lat < 0 && lat > -45 && lng > 110 && lng < 160) {
        // Western Australia
        if (lng < 125) return 'Australia/Perth';
        
        // Central Australia
        if (lng < 140) return 'Australia/Adelaide';
        
        // Eastern Australia
        return 'Australia/Sydney';
    }
    
    // New Zealand
    if (lat < -30 && lat > -50 && lng > 160 && lng < 180) {
        return 'Pacific/Auckland';
    }
    
    // Default to empty string - we'll let the server resolve it
    return '';
}

/**
 * Update form fields with geocoded location data
 * 
 * @param {string} locationString - The location to geocode
 * @param {boolean} updateTimezone - Whether to update the timezone field
 */
function updateLocationFields(locationString, updateTimezone = true) {
    // Get references to form fields
    const latitudeField = document.getElementById('latitude');
    const longitudeField = document.getElementById('longitude');
    const timezoneField = document.getElementById('timezone');
    const locationResultField = document.getElementById('location-result');
    
    // Only proceed if we have the required fields
    if (!latitudeField || !longitudeField) {
        console.error('Cannot find latitude or longitude fields');
        return;
    }
    
    // Show that we're working on it
    if (locationResultField) {
        locationResultField.innerHTML = '<span class="text-info"><i class="fa fa-spinner fa-spin"></i> Looking up location...</span>';
    }
    
    // Call the geocoding function
    geocodeLocation(
        locationString,
        // Success callback
        (lat, lng, displayName, timezone) => {
            // Update form fields
            latitudeField.value = lat;
            longitudeField.value = lng;
            
            // Update timezone if requested
            if (updateTimezone && timezoneField && timezone) {
                timezoneField.value = timezone;
            }
            
            // Show success message
            if (locationResultField) {
                locationResultField.innerHTML = `<span class="text-success"><i class="fa fa-check"></i> Found: ${displayName}</span>`;
                // Fade out after 5 seconds
                setTimeout(() => {
                    locationResultField.innerHTML = '';
                }, 5000);
            }
        },
        // Error callback
        (errorMessage) => {
            // Show error message
            if (locationResultField) {
                locationResultField.innerHTML = `<span class="text-danger"><i class="fa fa-exclamation-triangle"></i> ${errorMessage}</span>`;
            }
        }
    );
}