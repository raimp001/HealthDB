program research_data.aleo;

// Record to store research data hash and metadata
record ResearchData {
    owner: address,
    data_hash: field,
    timestamp: field,
    access_level: u8,
}

// Function to store new research data hash with timestamp
function store_data:
    input r0 as field.private;    // data hash
    input r1 as u8.private;       // access level
    // Get current time (simplified for now)
    cast self.caller r0 block.height r1 into r2 as ResearchData;
    output r2 as ResearchData.record;

// Function to verify data ownership
function verify_ownership:
    input r0 as ResearchData.record;
    assert.eq r0.owner self.caller;
    output true as boolean.public;

// Function to verify data timestamp
function verify_timestamp:
    input r0 as ResearchData.record;
    input r1 as field.public;     // timestamp to verify against
    assert.eq r0.timestamp r1;
    output true as boolean.public;
