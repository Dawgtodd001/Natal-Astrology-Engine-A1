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
        'los angeles': { lat: 34.0522, lng: -118.2437, name: 'Los Angeles, USA', timezone: 'America/Los_Angeles' },
        'chicago': { lat: 41.8781, lng: -87.6298, name: 'Chicago, USA', timezone: 'America/Chicago' },
        'paris': { lat: 48.8566, lng: 2.3522, name: 'Paris, France', timezone: 'Europe/Paris' }
    };
    
    // Check if any preset key is contained in the search string
    for (const key in presets) {
        if (search.includes(key) || key.includes(search)) {
            return presets[key];
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
    // Build the Nominatim API URL
    const apiUrl = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(locationString)}&limit=1`;
    
    // Make the request with proper headers
    fetch(apiUrl, {
        method: 'GET',
        headers: {
            'User-Agent': 'NatalAstrologyChart/1.0',
            'Accept': 'application/json'
        }
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
            const displayName = result.display_name;
            
            // Get timezone
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
    // This is a simplified approach - in reality we should use a timezone API
    // For now, make some basic estimates based on longitude
    
    // Rough timezone estimation based on longitude
    const hourOffset = Math.round(lng / 15);
    
    if (lng > -130 && lng < -65) {
        // North America
        if (lng < -115) return 'America/Los_Angeles';
        if (lng < -100) return 'America/Denver';
        if (lng < -85) return 'America/Chicago';
        return 'America/New_York';
    } else if (lng > -20 && lng < 25) {
        // Europe/Africa
        if (lng < 0) return 'Europe/London';
        if (lng < 15) return 'Europe/Paris';
        return 'Europe/Istanbul';
    } else if (lng > 100 && lng < 150) {
        // Australia/East Asia
        if (lng > 135) return 'Australia/Sydney';
        return 'Asia/Tokyo';
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